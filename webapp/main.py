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

app = FastAPI(title="Onto2AI Entitlement Manager", version="1.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class MembershipRequest(BaseModel):
    user_id: str
    group_id: str


class GroupPolicyRequest(BaseModel):
    group_id: str
    policy_id: str


class EntityMutationRequest(BaseModel):
    entity_type: str
    entity_id: str | None = None
    properties: Dict[str, Any] | None = None


def _neo4j_driver():
    cfg = get_config()["neo4j"]
    return GraphDatabase.driver(
        cfg["URL"],
        auth=(cfg["USERNAME"], cfg["PASSWORD"]),
    ), cfg["DATABASE"]


ENTITY_CONFIG = {
    "user": {
        "label": "User",
        "id_field": "userId",
        "name_field": None,
        "fields": [
            {"name": "userId", "label": "User ID", "required": True},
        ],
    },
    "group": {
        "label": "PolicyGroup",
        "id_field": "policyGroupId",
        "name_field": "policyGroupName",
        "fields": [
            {"name": "policyGroupId", "label": "Group ID", "required": True},
            {"name": "policyGroupName", "label": "Group Name", "required": False},
        ],
    },
    "policy": {
        "label": "Policy",
        "id_field": "policyId",
        "name_field": "policyName",
        "fields": [
            {"name": "policyId", "label": "Policy ID", "required": True},
            {"name": "policyName", "label": "Policy Name", "required": False},
            {"name": "definition", "label": "Definition", "required": False},
        ],
    },
    "table": {
        "label": "Table",
        "id_field": "tableId",
        "name_field": "tableName",
        "fields": [
            {"name": "tableId", "label": "Table ID", "required": True},
            {"name": "tableName", "label": "Table Name", "required": False},
        ],
    },
    "column": {
        "label": "Column",
        "id_field": "columnId",
        "name_field": "columnName",
        "fields": [
            {"name": "columnId", "label": "Column ID", "required": True},
            {"name": "columnName", "label": "Column Name", "required": False},
        ],
    },
    "database": {
        "label": "Schema",
        "id_field": "schemaId",
        "name_field": "schemaName",
        "fields": [
            {"name": "schemaId", "label": "Database ID", "required": True},
            {"name": "schemaName", "label": "Database Name", "required": False},
        ],
    },
}


def _entity_config(entity_type: str) -> Dict[str, str | None]:
    config = ENTITY_CONFIG.get(entity_type)
    if not config:
        raise HTTPException(status_code=400, detail=f"Unsupported entity type: {entity_type}")
    return config


def _graph_payload(limit: int = 1500) -> Dict[str, Any]:
    driver, database = _neo4j_driver()
    labels = ["User", "PolicyGroup", "Policy", "Schema", "Table", "Column"]
    rel_types = ["memberOf", "includesPolicy", "hasRowRule", "hasColumnRule", "belongsToTable", "belongsToSchema"]
    try:
        with driver.session(database=database) as session:
            node_rows = session.run(
                """
                MATCH (n)
                WHERE any(l IN labels(n) WHERE l IN $labels)
                RETURN n
                LIMIT $limit
                """,
                labels=labels,
                limit=limit,
            )
            link_rows = session.run(
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

            for row in node_rows:
                n = row["n"]
                node_id = n.element_id
                if node_id not in node_map:
                    n_labels = list(n.labels)
                    node_map[node_id] = {
                        "key": node_id,
                        "label": n_labels[0] if n_labels else "Node",
                        "labels": n_labels,
                        "properties": dict(n.items()),
                    }

            for row in link_rows:
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


@app.post("/api/entities/create")
def create_entity(req: EntityMutationRequest):
    config = _entity_config(req.entity_type)
    props = {k: v for k, v in (req.properties or {}).items() if isinstance(v, str) and v.strip()}
    entity_id = (req.entity_id or props.get(config["id_field"]) or "").strip()
    if not entity_id:
        raise HTTPException(status_code=400, detail="entity_id is required")

    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            props[config["id_field"]] = entity_id

            assignments = ", ".join(f"n.{key} = ${key}" for key in props)
            session.run(
                f"""
                MERGE (n:{config["label"]} {{{config["id_field"]}: ${config["id_field"]}}})
                SET {assignments}
                """,
                **props,
            ).consume()

            return {"ok": True, "action": "create", "entity_type": req.entity_type, "entity_id": entity_id}
    finally:
        driver.close()


@app.post("/api/entities/delete")
def delete_entity(req: EntityMutationRequest):
    config = _entity_config(req.entity_type)
    entity_id = (req.entity_id or "").strip()
    if not entity_id:
        raise HTTPException(status_code=400, detail="entity_id is required")

    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            summary = session.run(
                f"""
                MATCH (n:{config["label"]} {{{config["id_field"]}: $entity_id}})
                DETACH DELETE n
                RETURN count(n) AS deleted
                """,
                entity_id=entity_id,
            ).single()
            deleted = int(summary["deleted"]) if summary and summary["deleted"] is not None else 0
            return {
                "ok": True,
                "action": "delete",
                "entity_type": req.entity_type,
                "entity_id": entity_id,
                "deleted": deleted,
            }
    finally:
        driver.close()


@app.get("/api/entities/{entity_type}/meta")
def get_entity_meta(entity_type: str):
    config = _entity_config(entity_type)
    return {
        "entity_type": entity_type,
        "label": config["label"],
        "id_field": config["id_field"],
        "name_field": config["name_field"],
        "fields": config["fields"],
    }


@app.get("/api/entities/{entity_type}")
def list_entities(entity_type: str):
    config = _entity_config(entity_type)
    id_field = config["id_field"]
    name_field = config["name_field"]

    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            return_fields = [f"n.{id_field} AS entity_id"]
            if name_field:
                return_fields.append(f"n.{name_field} AS display_name")
            return_fields.append("properties(n) AS properties")
            order_field = name_field or id_field
            rows = session.run(
                f"""
                MATCH (n:{config["label"]})
                RETURN {", ".join(return_fields)}
                ORDER BY n.{order_field}, n.{id_field}
                """
            )
            return [
                {
                    "entity_id": r["entity_id"],
                    "display_name": r.get("display_name"),
                    "properties": r["properties"],
                }
                for r in rows
                if r["entity_id"]
            ]
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


@app.get("/api/users/{user_id}/group-options")
def get_user_group_options(user_id: str):
    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            rows = session.run(
                """
                MATCH (pg:PolicyGroup)
                OPTIONAL MATCH (u:User {userId: $user_id})-[r:memberOf]->(pg)
                RETURN
                  pg.policyGroupId AS groupId,
                  pg.policyGroupName AS groupName,
                  count(r) > 0 AS isMember
                ORDER BY groupName, groupId
                """,
                user_id=user_id,
            )
            entitle_to = []
            revoke_from = []
            for r in rows:
                item = {"group_id": r["groupId"], "group_name": r["groupName"]}
                if r["isMember"]:
                    revoke_from.append(item)
                else:
                    entitle_to.append(item)
            return {"user_id": user_id, "entitle_to": entitle_to, "revoke_from": revoke_from}
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


@app.get("/api/groups/{group_id}/user-options")
def get_group_user_options(group_id: str):
    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            exists = session.run(
                "MATCH (pg:PolicyGroup {policyGroupId: $group_id}) RETURN pg.policyGroupId AS id",
                group_id=group_id,
            ).single()
            if not exists:
                raise HTTPException(status_code=404, detail=f"PolicyGroup not found: {group_id}")

            rows = session.run(
                """
                MATCH (p:Policy)
                OPTIONAL MATCH (:PolicyGroup {policyGroupId: $group_id})-[r:includesPolicy]->(p)
                RETURN
                  p.policyId AS policyId,
                  p.policyName AS policyName,
                  p.definition AS definition,
                  count(r) > 0 AS isIncluded
                ORDER BY policyName, policyId
                """,
                group_id=group_id,
            )
            including_policies = []
            excluding_policies = []
            for r in rows:
                policy_id = r["policyId"]
                if not policy_id:
                    continue
                item = {
                    "policy_id": policy_id,
                    "policy_name": r["policyName"],
                    "definition": r["definition"],
                }
                if r["isIncluded"]:
                    excluding_policies.append(item)
                else:
                    including_policies.append(item)
            return {
                "group_id": group_id,
                "including_policies": including_policies,
                "excluding_policies": excluding_policies,
            }
    finally:
        driver.close()


@app.post("/api/groups/includes-policy")
def include_policy_for_group(req: GroupPolicyRequest):
    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            found = session.run(
                """
                MATCH (pg:PolicyGroup {policyGroupId: $group_id}), (p:Policy {policyId: $policy_id})
                RETURN pg.policyGroupId AS groupId, p.policyId AS policyId
                """,
                group_id=req.group_id,
                policy_id=req.policy_id,
            ).single()
            if not found:
                raise HTTPException(
                    status_code=404,
                    detail=f"PolicyGroup or Policy not found: {req.group_id}, {req.policy_id}",
                )

            session.run(
                """
                MATCH (pg:PolicyGroup {policyGroupId: $group_id})
                MATCH (p:Policy {policyId: $policy_id})
                MERGE (pg)-[:includesPolicy]->(p)
                """,
                group_id=req.group_id,
                policy_id=req.policy_id,
            ).consume()
            return {"ok": True, "action": "include", "group_id": req.group_id, "policy_id": req.policy_id}
    finally:
        driver.close()


@app.post("/api/groups/excludes-policy")
def exclude_policy_for_group(req: GroupPolicyRequest):
    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            found = session.run(
                """
                MATCH (pg:PolicyGroup {policyGroupId: $group_id}), (p:Policy {policyId: $policy_id})
                RETURN pg.policyGroupId AS groupId, p.policyId AS policyId
                """,
                group_id=req.group_id,
                policy_id=req.policy_id,
            ).single()
            if not found:
                raise HTTPException(
                    status_code=404,
                    detail=f"PolicyGroup or Policy not found: {req.group_id}, {req.policy_id}",
                )

            summary = session.run(
                """
                MATCH (pg:PolicyGroup {policyGroupId: $group_id})-[r:includesPolicy]->(p:Policy {policyId: $policy_id})
                DELETE r
                RETURN count(r) AS deleted
                """,
                group_id=req.group_id,
                policy_id=req.policy_id,
            ).single()
            deleted = int(summary["deleted"]) if summary and summary["deleted"] is not None else 0
            return {
                "ok": True,
                "action": "exclude",
                "group_id": req.group_id,
                "policy_id": req.policy_id,
                "deleted": deleted,
            }
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
