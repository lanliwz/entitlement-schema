from langgraph.graph import StateGraph, START, END
from relational_database.mysql.mysql_entitlement_util import *
from relational_database.mysql.mysql_entitlement_util import _effective_entitlements_for_user
from secret.secret_util import *
config = get_config()

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


def summarize_effective_entitlements(res: AppState) -> list[str]:
    summaries = []
    entitlements_by_table = res.get("entitlements_by_table", {}) or {}
    user_groups = res.get("user_groups", []) or []
    effective = _effective_entitlements_for_user(entitlements_by_table, user_groups)
    for table_key, entitlements in effective.items():
        if not entitlements:
            summaries.append(f"{table_key}: no active row or mask rules")
            continue
        parts = []
        for entitlement in entitlements:
            rule_type = entitlement.get("ruleType", "UNKNOWN")
            column_name = entitlement.get("columnName", "?")
            definition = entitlement.get("policyDefinition", "")
            parts.append(f"{rule_type}:{column_name}:{definition}")
        summaries.append(f"{table_key}: " + " | ".join(parts))
    return summaries


def show(user_id: str, sql: str):
    print("="*80)
    print(f"USER: {user_id}")
    print("INPUT SQL:")
    print(sql.strip())
    res = run_query(user_id, sql)
    print("\nCURRENT GROUPS:")
    user_groups = res.get("user_groups", [])
    if user_groups:
        for group_name in user_groups:
            print("•", group_name)
    else:
        print("• None")
    print("\nCURRENT EFFECTIVE ENTITLEMENTS:")
    for summary in summarize_effective_entitlements(res):
        print("•", summary)
    print("\nREWRITTEN SQL:")
    print(res.get("rewritten_sql"))
    print("\nTRACE:")
    for m in res.get("messages", []):
        print("•", m)
    print("\nROWS:")
    for row in res.get("rows", []):
        print(row)

if __name__ == "__main__":
    q = """
    SELECT e.emp_id, e.first_name, e.last_name, e.salary, d.dept_name
    FROM bank.employee e
    JOIN bank.department d ON e.dept_id = d.dept_id
    ORDER BY e.emp_id
    """

    show("user-alice", q)
    show("user-bob",   q)
    show("user-carol", q)
    show("user-sam",   q)
    show("user-tom",   q)
