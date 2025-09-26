from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from relational_database.mysql.mysql_entitlement_util import *




from graph_database.entitlement_util import EntitlementRepository

# ---- MySQL executor --------------------------------------------------
def run_mysql_query(sql: str) -> List[Dict[str, Any]]:
    cur = mysql_conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()


# ---- Helpers ---------------------------------------------------------
def _append_msg(state: AppState, msg: str) -> None:
    state.setdefault("messages", []).append(msg)

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

def fetch_all_entitlements_for_tables(user_id: str, parsed_tables: List[Dict[str, str]]) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    """
    Returns a dict keyed by (schema, table) -> [entitlements...]
    If schema is None, default to 'bank'.
    """
    neo4j_bolt_url = os.getenv("Neo4jFinDBUrl")
    username = os.getenv("Neo4jFinDBUserName")
    password = os.getenv("Neo4jFinDBPassword")

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

def rule_based_rewrite_all(original_sql: str,
                           parsed_tables: List[Dict[str, str]],
                           entitlements_by_table: Dict[Tuple[str, str], List[Dict[str, Any]]]) -> str:
    """
    Light, alias-aware transformer using sqlglot:
      - Apply ROW filters (supports dept_name = 'X') on proper table alias
      - Mask salary in SELECT for employee table when a MASK entitlement exists
    """
    expr = parse_one(original_sql, read="mysql")

    # Build alias map observed in the actual SQL
    alias_map = _build_alias_map(expr)

    # 1) Apply ROW filters (dept_name = '...') table-aware
    row_preds: List[E.Expression] = []
    for (schema, table), ents in entitlements_by_table.items():
        sch_key = schema if schema != "" else None
        alias = alias_map.get((sch_key, table))
        # support simple rule definitions like "dept_name = 'Finance'"
        for e in ents:
            if e.get("ruleType") == "ROW" and e.get("columnName") == "dept_name":
                definition = (e.get("policyDefinition") or e.get("policyDefinition") or e.get("definition") or "").strip()
                # naive parse of RHS between '=' and end (or 'AND'…), keep quoted if present
                if "dept_name" in definition and "=" in definition:
                    rhs = definition.split("=", 1)[1].strip()
                    # Normalize quotes (if missing)
                    if not rhs.startswith(("'", '"')):
                        rhs = f"'{rhs.strip()}'"
                    col = E.Column(this=E.Identifier(this="dept_name"))
                    if alias:
                        col = E.Column(this=E.Identifier(this="dept_name"), table=E.Identifier(this=alias))
                    pred = E.EQ(this=col, expression=E.Var(this=rhs.strip("'").strip('"')))
                    # Use a quoted string literal properly:
                    pred = E.EQ(this=col, expression=E.Literal.string(rhs.strip("'").strip('"')))
                    row_preds.append(pred)

    if row_preds:
        # Combine all row filters with AND
        combined = row_preds[0]
        for p in row_preds[1:]:
            combined = E.And(this=combined, expression=p)
        _and_where(expr, combined)

    # 2) Apply MASK for salary (replace any SELECT item that references salary from employee table)
    # If employee table present and has MASK on 'salary'
    mask_needed = False
    for (schema, table), ents in entitlements_by_table.items():
        if table == "employee" and any(e.get("ruleType") == "MASK" and e.get("columnName") == "salary" for e in ents):
            mask_needed = True
            employee_alias = alias_map.get((schema if schema != "" else None, "employee"))
            break

    if mask_needed:
        select = expr.args.get("expressions") or expr.args.get("select")
        # sqlglot SELECT list is under expr.args['expressions'] (list of E.Expression)
        select_expressions = expr.expressions
        new_exprs: List[E.Expression] = []
        for item in select_expressions:
            # Detect columns named salary, with or without alias qualification
            col: E.Column | None = item.this if isinstance(item, E.Alias) and isinstance(item.this, E.Column) else (item if isinstance(item, E.Column) else None)
            alias_name = None
            if isinstance(item, E.Alias) and item.alias:
                alias_name = str(item.alias)
            if isinstance(item, E.Alias):
                inner = item.this
            else:
                inner = item

            is_salary = False
            if isinstance(inner, E.Column) and str(inner.this).lower() == "salary":
                # If employee alias exists, ensure column is unqualified or matches that alias
                tname = str(inner.table) if inner.table else None
                if not employee_alias or tname is None or tname == employee_alias:
                    is_salary = True

            if mask_needed and is_salary:
                masked = E.Alias(
                    this=E.Literal.number("0.00"),
                    alias=E.Identifier(this="salary")
                )
                new_exprs.append(masked)
            else:
                new_exprs.append(item)

        expr.set("expressions", new_exprs)

    return expr.sql(dialect="mysql")

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
    user = "user-alice"
    # user = "user-bob"
    q = """
    SELECT e.emp_id, e.first_name, e.last_name, e.salary
    FROM bank.employee e
    JOIN bank.department d ON e.dept_id = d.dept_id
    """
    result = run_query(user, q)
    print("---- TRACE ----")
    for m in result.get("messages", []):
        print("•", m)
    print("\n---- REWRITTEN SQL ----")
    print(result.get("rewritten_sql"))
    print("\n---- ROWS ----")
    for row in result.get("rows", []):
        print(row)