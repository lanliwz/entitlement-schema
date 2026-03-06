from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from neo4j import GraphDatabase
from pydantic import BaseModel

from secret.secret_util import get_config


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Entitlement Graph Explorer", version="1.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class MembershipRequest(BaseModel):
    user_id: str
    group_id: str


def _neo4j_driver():
    cfg = get_config()["neo4j"]
    return GraphDatabase.driver(
        cfg["URL"],
        auth=(cfg["USERNAME"], cfg["PASSWORD"]),
    ), cfg["DATABASE"]


def _graph_payload(limit: int = 1500) -> Dict[str, Any]:
    driver, database = _neo4j_driver()
    labels = ["User", "PolicyGroup", "Policy", "Schema", "Table", "Column"]
    rel_types = ["memberOf", "includesPolicy", "hasRowRule", "hasColumnRule", "belongsToTable", "belongsToSchema"]
    try:
        with driver.session(database=database) as session:
            rows = session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE any(l IN labels(a) WHERE l IN $labels)
                  AND any(l IN labels(b) WHERE l IN $labels)
                  AND type(r) IN $rel_types
                RETURN a, r, b
                LIMIT $limit
                """,
                labels=labels,
                rel_types=rel_types,
                limit=limit,
            )

            node_map: Dict[str, Dict[str, Any]] = {}
            links: List[Dict[str, Any]] = []
            rel_seen = set()

            for row in rows:
                a = row["a"]
                b = row["b"]
                r = row["r"]
                a_id = a.element_id
                b_id = b.element_id
                r_id = r.element_id

                if a_id not in node_map:
                    a_labels = list(a.labels)
                    node_map[a_id] = {
                        "key": a_id,
                        "label": a_labels[0] if a_labels else "Node",
                        "labels": a_labels,
                        "properties": dict(a.items()),
                    }
                if b_id not in node_map:
                    b_labels = list(b.labels)
                    node_map[b_id] = {
                        "key": b_id,
                        "label": b_labels[0] if b_labels else "Node",
                        "labels": b_labels,
                        "properties": dict(b.items()),
                    }
                if r_id not in rel_seen:
                    rel_seen.add(r_id)
                    links.append(
                        {
                            "key": r_id,
                            "from": a_id,
                            "to": b_id,
                            "type": r.type,
                            "properties": dict(r.items()),
                        }
                    )

            return {"nodes": list(node_map.values()), "links": links}
    finally:
        driver.close()


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/graph")
def get_graph(limit: int = 1500):
    return _graph_payload(limit=limit)


@app.get("/api/users")
def get_users():
    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            rows = session.run(
                """
                MATCH (u:User)
                RETURN u.userId AS userId
                ORDER BY userId
                """
            )
            return [{"user_id": r["userId"]} for r in rows if r["userId"]]
    finally:
        driver.close()


@app.get("/api/groups")
def get_groups():
    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            rows = session.run(
                """
                MATCH (pg:PolicyGroup)
                RETURN pg.policyGroupId AS groupId, pg.policyGroupName AS groupName
                ORDER BY groupName, groupId
                """
            )
            return [
                {
                    "group_id": r["groupId"],
                    "group_name": r["groupName"],
                }
                for r in rows
                if r["groupId"]
            ]
    finally:
        driver.close()


@app.post("/api/entitlements/assign")
def assign_user_to_group(req: MembershipRequest):
    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            found = session.run(
                "MATCH (pg:PolicyGroup {policyGroupId: $group_id}) RETURN pg.policyGroupId AS id",
                group_id=req.group_id,
            ).single()
            if not found:
                raise HTTPException(status_code=404, detail=f"PolicyGroup not found: {req.group_id}")

            session.run(
                """
                MERGE (u:User {userId: $user_id})
                WITH u
                MATCH (pg:PolicyGroup {policyGroupId: $group_id})
                MERGE (u)-[:memberOf]->(pg)
                """,
                user_id=req.user_id,
                group_id=req.group_id,
            ).consume()
            return {"ok": True, "action": "assign", "user_id": req.user_id, "group_id": req.group_id}
    finally:
        driver.close()


@app.post("/api/entitlements/revoke")
def revoke_user_from_group(req: MembershipRequest):
    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            summary = session.run(
                """
                MATCH (u:User {userId: $user_id})-[r:memberOf]->(pg:PolicyGroup {policyGroupId: $group_id})
                DELETE r
                RETURN count(r) AS deleted
                """,
                user_id=req.user_id,
                group_id=req.group_id,
            ).single()
            deleted = int(summary["deleted"]) if summary and summary["deleted"] is not None else 0
            return {
                "ok": True,
                "action": "revoke",
                "user_id": req.user_id,
                "group_id": req.group_id,
                "deleted": deleted,
            }
    finally:
        driver.close()
