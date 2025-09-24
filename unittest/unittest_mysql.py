from __future__ import annotations
from relational_database.mysql.mysql_connection import *
from graph_database.entitlement_util import *
import os
from typing import Any, Dict, List, Literal, TypedDict

import sqlglot
from sqlglot import parse_one
from langgraph.graph import StateGraph, START, END

mysql_conn = mysql_connection()
# print(mysql_query("select * from bank.employee",mysql_conn))


# Optional LLM rewriter (falls back to rule-based if no key)
try:
    from langchain_openai import ChatOpenAI
    HAVE_LLM = bool(os.getenv("OPENAI_API_KEY"))
except Exception:
    HAVE_LLM = False

# ---- Neo4j Entitlement repo (minimal subset needed) -----------------
from neo4j import GraphDatabase

class EntitlementRepository:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    def close(self):
        self.driver.close()

    def fetch_entitlements(self, user_id: str, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        cypher = """
        MATCH (u:User {userId: $userId})-[:memberOf]->(pg:PolicyGroup)-[:includesPolicy]->(p:Policy)
        MATCH (t:Table {tableName: $tableName})-[:belongsToSchema]->(s:Schema {schemaName: $schemaName})
        MATCH (c:Column)-[:belongsToTable]->(t)
        MATCH (p)-[r:hasRowRule|hasColumnRule]->(c)
        RETURN DISTINCT
          u.userId AS userId,
          s.schemaName AS schemaName,
          t.tableName AS tableName,
          c.columnId AS columnId,
          c.columnName AS columnName,
          p.policyId AS policyId,
          p.policyName AS policyName,
          p.definition AS policyDefinition,
          pg.policyGroupId AS policyGroupId,
          pg.policyGroupName AS policyGroupName,
          CASE type(r)
            WHEN 'hasRowRule' THEN 'ROW'
            WHEN 'hasColumnRule' THEN 'MASK'
          END AS ruleType
        ORDER BY c.columnName, ruleType, p.policyName;
        """
        with self.driver.session() as session:
            rs = session.run(
                cypher,
                userId=user_id,
                schemaName=schema_name,
                tableName=table_name
            )
            return [dict(r) for r in rs]

# ---- MySQL executor --------------------------------------------------

def run_mysql_query(sql: str) -> List[Dict[str, Any]]:

    try:
        cur = mysql_conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        # mysql_conn.commit()
        return rows
    finally:
        cur.close()
        # mysql_conn.close()

# ---- App State -------------------------------------------------------
class AppState(TypedDict, total=False):
    user_id: str
    input_sql: str
    parsed_tables: List[Dict[str, str]]  # [{schema, table}]
    entitlements: List[Dict[str, Any]]   # raw from Neo4j
    rewritten_sql: str
    rows: List[Dict[str, Any]]
    messages: List[str]                  # trace/debug

# ---- Helpers ---------------------------------------------------------
def _append_msg(state: AppState, msg: str) -> None:
    state.setdefault("messages", []).append(msg)

def parse_tables(sql: str) -> List[Dict[str, str]]:
    """
    Use sqlglot to extract table references with optional schema.
    Supports common SELECT/INSERT/UPDATE/DELETE.
    """
    try:
        expr = parse_one(sql, read="mysql")
    except Exception:
        # try generic
        expr = parse_one(sql)
    tables = []
    for t in expr.find_all(sqlglot.exp.Table):
        # t.this is table, t.db is schema (can be None)
        table = t.this
        schema = t.db
        tables.append({
            "schema": str(schema) if schema else None,
            "table": str(table) if table else None
        })
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for item in tables:
        key = (item["schema"], item["table"])
        if key not in seen and item["table"]:
            deduped.append(item)
            seen.add(key)
    return deduped

def choose_primary_table(parsed: List[Dict[str, str]], default_schema: str | None = None) -> Dict[str, str]:
    """
    For this POC we focus on the first table encountered.
    If no schema is present, use default_schema (if provided).
    """
    if not parsed:
        raise ValueError("No table found in SQL.")
    primary = dict(parsed[0])
    if not primary.get("schema"):
        primary["schema"] = default_schema
    if not primary["schema"]:
        # last resort default (adjust for your environment)
        primary["schema"] = "bank"
    return primary

# ---- Rewriter (LLM or fallback) -------------------------------------
REWRITER_SYSTEM_PROMPT = """You are a precise SQL rewriter that applies entitlement rules.
You receive the user's original SQL and a set of entitlements (row filters and column masks).
- Apply ALL row filters by conjoining them (AND) into WHERE (or ON) clauses scoped to the correct table/aliases.
- Apply column MASK by replacing the selected column expressions with a masked expression (e.g., 0.00 AS salary) if masking applies.
- Preserve other query semantics, table aliases, ordering, limits, joins, and selected columns.
Return only the final SQL, no commentary.
"""

def rule_based_rewrite(original_sql: str, entitlements: List[Dict[str, Any]]) -> str:
    """
    Very small fallback:
    - If any ROW entitlement on column 'dept_name' with definition containing "= 'X'",
      append WHERE dept_name = 'X' (or AND ... if WHERE exists).
    - If any MASK entitlement on 'salary', naively replace 'salary' in SELECT list with '0.00 AS salary'
      (This is simplistic; in real usage, prefer the LLM branch for robust rewriting.)
    """
    sql = original_sql

    # Row rules (dept_name)
    row_rules = [e for e in entitlements if e.get("ruleType") == "ROW" and e.get("columnName") == "dept_name"]
    filters = []
    for r in row_rules:
        definition = (r.get("policyDefinition") or r.get("policyDefinition") or r.get("definition") or "").strip()
        # crude extraction of "dept_name = 'X'"
        if "dept_name" in definition and "=" in definition:
            # Extract right-hand quoted value
            try:
                rhs = definition.split("=")[1].strip()
                # ensure quotes
                if not rhs.startswith(("'", '"')):
                    rhs = f"'{rhs}'"
                filters.append(f"dept_name = {rhs}")
            except Exception:
                pass
    if filters:
        clause = " AND ".join(filters)
        lower = sql.lower()
        if " where " in lower:
            sql = sql.replace(sql[lower.find(" where "):], f" WHERE ({clause}) AND " + sql[lower.find(" where ") + 7:])
        else:
            # place before GROUP/ORDER/LIMIT if present
            tokens = [" group by ", " order by ", " limit "]
            lower = sql.lower()
            insert_at = len(sql)
            for tok in tokens:
                pos = lower.find(tok)
                if pos != -1:
                    insert_at = min(insert_at, pos)
            sql = sql[:insert_at] + f" WHERE {clause} " + sql[insert_at:]

    # Mask rules (salary)
    mask_rules = [e for e in entitlements if e.get("ruleType") == "MASK" and e.get("columnName") == "salary"]
    if mask_rules:
        # naive: replace " salary" in SELECT list with " 0.00 AS salary"
        # Caution: simplistic; for robust behavior rely on LLM or a real SQL AST rewriter.
        sql = sql.replace(" salary", " 0.00 AS salary")

    return sql

def llm_rewrite(original_sql: str, entitlements: List[Dict[str, Any]]) -> str:
    if not HAVE_LLM:
        return rule_based_rewrite(original_sql, entitlements)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    content = {
        "original_sql": original_sql,
        "entitlements": entitlements,
    }
    msg = llm.invoke([
        {"role": "system", "content": REWRITER_SYSTEM_PROMPT},
        {"role": "user", "content": str(content)}
    ])
    # LangChain returns an AIMessage with .content
    return msg.content.strip()

# ---- Nodes -----------------------------------------------------------
def parse_node(state: AppState) -> AppState:
    _append_msg(state, "Parsing SQL for table references.")
    parsed = parse_tables(state["input_sql"])
    state["parsed_tables"] = parsed
    prim = choose_primary_table(parsed, default_schema=None)
    _append_msg(state, f"Primary table resolved: {prim['schema']}.{prim['table']}")
    return state

def entitlements_node(state: AppState) -> AppState:
    prim = choose_primary_table(state["parsed_tables"], default_schema=None)
    schema_name, table_name = prim["schema"], prim["table"]
    if not schema_name:
        schema_name = "bank"  # default, adjust if you prefer to require explicit schema
    _append_msg(state, f"Fetching entitlements for user={state['user_id']} on {schema_name}.{table_name}")

    neo4j_bolt_url = os.getenv("Neo4jFinDBUrl")
    username = os.getenv("Neo4jFinDBUserName")
    password = os.getenv("Neo4jFinDBPassword")

    repo = EntitlementRepository(
        neo4j_bolt_url,
        username,
        password
    )
    try:
        ents = repo.fetch_entitlements(state["user_id"], schema_name, table_name)
    finally:
        repo.close()

    state["entitlements"] = ents
    _append_msg(state, f"Fetched {len(ents)} entitlements.")
    return state

def rewrite_node(state: AppState) -> AppState:
    _append_msg(state, "Rewriting SQL using entitlements.")
    rewritten = llm_rewrite(state["input_sql"], state.get("entitlements", []))
    state["rewritten_sql"] = rewritten
    return state

def execute_node(state: AppState) -> AppState:
    _append_msg(state, "Executing rewritten SQL in MySQL.")
    rows = run_mysql_query(state["rewritten_sql"])
    state["rows"] = rows
    _append_msg(state, f"Returned {len(rows)} rows.")
    return state

# ---- Graph wiring ----------------------------------------------------
def build_app():
    g = StateGraph(AppState)
    g.add_node("parse", parse_node)
    g.add_node("entitlements", entitlements_node)
    g.add_node("rewrite", rewrite_node)
    g.add_node("execute", execute_node)

    g.add_edge(START, "parse")
    g.add_edge("parse", "entitlements")
    g.add_edge("entitlements", "rewrite")
    g.add_edge("rewrite", "execute")
    g.add_edge("execute", END)
    return g.compile()

# ---- Runner ----------------------------------------------------------
def run_query(user_id: str, sql: str) -> AppState:
    app = build_app()
    initial: AppState = {"user_id": user_id, "input_sql": sql}
    return app.invoke(initial)

# ---- Example ---------------------------------------------------------
if __name__ == "__main__":
    # Example user + query
    # Try something like:
    #   SELECT emp_id, first_name, last_name, salary FROM bank.employee;
    #
    # If your entitlements include a MASK on salary for this user,
    # the rewriter (LLM or fallback) should alter the SELECT appropriately.
    user = os.getenv("TEST_USER_ID", "user-alice")
    q = os.getenv("TEST_SQL", "SELECT emp_id, first_name, last_name, salary FROM bank.employee")

    result = run_query(user, q)
    print("---- TRACE ----")
    for m in result.get("messages", []):
        print("•", m)
    print("\n---- REWRITTEN SQL ----")
    print(result.get("rewritten_sql"))
    print("\n---- ROWS ----")
    for row in result.get("rows", []):
        print(row)