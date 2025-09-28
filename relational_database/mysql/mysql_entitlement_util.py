from graph_database.entitlement_util import *
import sqlglot
from sqlglot import parse_one
from sqlglot import exp as E
from typing import Any, Dict, List, Tuple, TypedDict
import re
from relational_database.mysql.mysql_connection import mysql_connection

mysql_conn = mysql_connection()

def get_sql(text: str) -> str:
    """
    If input text is a raw SQL statement, return it directly.
    If wrapped in ```sql ... ```, extract the SQL inside.
    Otherwise, return an empty string.
    """
    sql_keywords = ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER")
    stripped = text.strip()
    if any(stripped.upper().startswith(k) for k in sql_keywords):
        return stripped
    match = re.search(r"```sql(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def llm_rewrite_all(original_sql, parsed_tables, entitlements_by_table):
    REWRITER_SYSTEM_PROMPT = """You are a precise SQL rewriter that applies entitlement rules for ALL tables in the query.
    Input contains: original SQL, parsed tables (with aliases), and entitlements_by_table keyed by (schema, table).
    Rules:
    - For each table's entitlements:
      * Add row filters by AND-conjoining them into WHERE/ON clauses using the correct table alias.
      * Apply column masks by replacing selected column expressions with masked expressions (e.g. 0.00 AS salary) when masking applies.
    - Preserve joins, aliases, projections, order, limits.
    Return only the final SQL, no commentary.
    """
    # Optional LLM rewriter (falls back to rule-based if no key)
    try:
        from langchain_openai import ChatOpenAI
        HAVE_LLM = bool(os.getenv("OPENAI_API_KEY"))
    except Exception:
        HAVE_LLM = False
    if not HAVE_LLM:
        return rule_based_rewrite_all(original_sql, parsed_tables, entitlements_by_table)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    payload = {
        "original_sql": original_sql,
        "tables": parsed_tables,
        "entitlements_by_table": entitlements_by_table,  # string-keyed dict
    }
    msg = llm.invoke([
        {"role": "system", "content": REWRITER_SYSTEM_PROMPT},
        {"role": "user", "content": str(payload)}
    ])
    return msg.content.strip()

def fetch_all_entitlements_for_tables(user_id: str, parsed_tables: List[Dict[str, str]]) -> Dict[str, List[Dict[str, Any]]]:
    repo = EntitlementRepository()
    out: Dict[str, List[Dict[str, Any]]] = {}
    try:
        for t in parsed_tables:
            schema = t["schema"] or "bank"
            table = t["table"]
            key = f"{schema}.{table}"              # <-- string key
            if key not in out:
                out[key] = repo.fetch_entitlements(user_id, schema, table)
    finally:
        repo.close()
    return out

def rule_based_rewrite_all(original_sql: str,
                           parsed_tables: List[Dict[str, str]],
                           entitlements_by_table: Dict[str, List[Dict[str, Any]]]) -> str:
    expr = parse_one(original_sql, read="mysql")

    # build alias map: (schema, table) -> alias (internal tuples ok, not stored in state)
    alias_map = {}
    for t in expr.find_all(sqlglot.exp.Table):
        schema = str(t.db) if t.db else None
        table  = str(t.this) if t.this else None
        alias_exp = t.args.get("alias")
        alias = str(alias_exp.this) if (alias_exp and alias_exp.this) else None
        if table:
            alias_map[(schema, table)] = alias

    # ROW filters
    row_preds = []
    for key, ents in entitlements_by_table.items():
        # key format "schema.table"
        schema, table = key.split(".", 1)
        schema = schema or None
        alias = alias_map.get((schema, table))
        for e in ents:
            if e.get("ruleType") == "ROW" and e.get("columnName") == "dept_name":
                definition = (e.get("policyDefinition") or e.get("definition") or "").strip()
                if "dept_name" in definition and "=" in definition:
                    rhs = definition.split("=", 1)[1].strip().strip(";")
                    if not rhs.startswith(("'", '"')):
                        rhs = f"'{rhs}'"
                    col = E.Column(this=E.Identifier(this="dept_name"))
                    if alias:
                        col = E.Column(this=E.Identifier(this="dept_name"), table=E.Identifier(this=alias))
                    pred = E.EQ(this=col, expression=E.Literal.string(rhs.strip("'").strip('"')))
                    row_preds.append(pred)

    if row_preds:
        combined = row_preds[0]
        for p in row_preds[1:]:
            combined = E.And(this=combined, expression=p)
        where = expr.args.get("where")
        if where and where.this:
            where.this = E.And(this=where.this, expression=combined)
        else:
            expr.set("where", E.Where(this=combined))

    # MASK salary
    mask_needed = False
    emp_alias = None
    for key, ents in entitlements_by_table.items():
        _, table = key.split(".", 1)
        if table == "employee" and any(e.get("ruleType") == "MASK" and e.get("columnName") == "salary" for e in ents):
            mask_needed = True
            # find alias for employee
            for (sch, tbl), a in alias_map.items():
                if tbl == "employee":
                    emp_alias = a
                    break
            break

    if mask_needed:
        new_exprs = []
        for item in expr.expressions:
            inner = item.this if isinstance(item, E.Alias) else item
            is_salary = isinstance(inner, E.Column) and str(inner.this).lower() == "salary"
            if is_salary:
                tname = str(inner.table) if inner.table else None
                if emp_alias is None or tname is None or tname == emp_alias:
                    masked = E.Alias(this=E.Literal.number("0.00"), alias=E.Identifier(this="salary"))
                    new_exprs.append(masked)
                    continue
            new_exprs.append(item)
        expr.set("expressions", new_exprs)

    return expr.sql(dialect="mysql")

class AppState(TypedDict, total=False):
    user_id: str
    input_sql: str
    parsed_tables: List[Dict[str, str]]
    entitlements_by_table: Dict[str, List[Dict[str, Any]]]  # <-- string keys
    rewritten_sql: str
    rows: List[Dict[str, Any]]
    messages: List[str]
# ---- MySQL executor --------------------------------------------------
def run_mysql_query(sql: str) -> List[Dict[str, Any]]:
    cur = mysql_conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
def fetch_all_entitlements_for_tables(user_id: str, parsed_tables: List[Dict[str, str]]) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    """
    Returns a dict keyed by (schema, table) -> [entitlements...]
    If schema is None, default to 'bank'.
    """

    repo = EntitlementRepository()
    out: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    try:
        for t in parsed_tables:
            schema = t["schema"] or "bank"
            table = t["table"]
            key = (schema, table)
            if key not in out:
                out[key] = repo.fetch_entitlements(user_id, schema, table)
    finally:
        repo.close()
    return out
def parse_tables(sql: str) -> List[Dict[str, str]]:
    """
    Extract (schema, table, alias) for all table refs in the query.
    """
    try:
        expr = parse_one(sql, read="mysql")
    except Exception:
        expr = parse_one(sql)
    out: List[Dict[str, str]] = []
    for t in expr.find_all(sqlglot.exp.Table):
        table = str(t.this) if t.this else None
        schema = str(t.db) if t.db else None
        alias_exp: E.Alias = t.args.get("alias")
        alias = str(alias_exp.this) if (alias_exp and alias_exp.this) else None
        if table:
            out.append({"schema": schema, "table": table, "alias": alias})
    # dedupe by (schema, table, alias)
    seen = set()
    deduped = []
    for x in out:
        key = (x["schema"], x["table"], x["alias"])
        if key not in seen:
            deduped.append(x); seen.add(key)
    return deduped
# ---- Helpers ---------------------------------------------------------
def _append_msg(state: AppState, msg: str) -> None:
    state.setdefault("messages", []).append(msg)



# ---- AST helpers for alias mapping and rewriting --------------------
def _build_alias_map(expr: E.Expression) -> Dict[Tuple[str|None, str], str|None]:
    """
    Map (schema, table) -> alias (or None if no alias).
    """
    amap: Dict[Tuple[str|None, str], str|None] = {}
    for t in expr.find_all(E.Table):
        schema = str(t.db) if t.db else None
        table = str(t.this) if t.this else None
        alias_exp: E.Alias = t.args.get("alias")
        alias = str(alias_exp.this) if (alias_exp and alias_exp.this) else None
        if table:
            amap[(schema, table)] = alias
    return amap

def _and_where(expr: E.Expression, pred: E.Expression) -> None:
    """
    AND-conjoin a predicate into the query's WHERE clause.
    If WHERE absent, create one; try to insert before GROUP/ORDER/LIMIT automatically via sqlglot.
    """
    where = expr.args.get("where")
    if where and where.this:
        where.this = E.And(this=where.this, expression=pred)
    else:
        expr.set("where", E.Where(this=pred))
# ---- Nodes -----------------------------------------------------------
def parse_node(state: AppState) -> AppState:
    _append_msg(state, "Parsing SQL for table references (multi-table, alias-aware).")
    parsed = parse_tables(state["input_sql"])
    state["parsed_tables"] = parsed
    _append_msg(state, f"Tables found: {parsed}")
    return state

def entitlements_node(state: AppState) -> AppState:
    _append_msg(state, "Fetching entitlements for all tables.")
    ent_by_tbl = fetch_all_entitlements_for_tables(state["user_id"], state["parsed_tables"])
    state["entitlements_by_table"] = ent_by_tbl
    _append_msg(state, f"Fetched entitlements for {len(ent_by_tbl)} table(s).")
    return state

def rewrite_node(state: AppState) -> AppState:
    _append_msg(state, "Rewriting SQL using entitlements across all tables.")
    rewritten = llm_rewrite_all(
        state["input_sql"],
        state.get("parsed_tables", []),
        state.get("entitlements_by_table", {})
    )
    state["rewritten_sql"] = rewritten
    return state

def execute_node(state: AppState) -> AppState:
    _append_msg(state, "Executing rewritten SQL in MySQL.")
    rewritten_sql = get_sql(state["rewritten_sql"])
    rows = run_mysql_query(rewritten_sql)
    state["rows"] = rows
    _append_msg(state, f"Returned {len(rows)} rows.")
    return state


