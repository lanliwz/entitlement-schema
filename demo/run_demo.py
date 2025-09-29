from langgraph.graph import StateGraph, START, END
from relational_database.mysql.mysql_entitlement_util import *
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

def show(user_id: str, sql: str):
    print("="*80)
    print(f"USER: {user_id}")
    print("INPUT SQL:")
    print(sql.strip())
    res = run_query(user_id, sql)
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

    show("user-alice", q)  # Finance rows only; salary masked
    show("user-bob",   q)  # All rows; no masking (Client Support)
    show("user-carol", q)  # IT rows only; salary masked