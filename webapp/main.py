from __future__ import annotations

import json
import os
import re
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


class ChatExplorerRequest(BaseModel):
    question: str


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


def _known_labels() -> List[str]:
    return ["User", "PolicyGroup", "Policy", "Schema", "Table", "Column"]


def _known_rel_types() -> List[str]:
    return ["memberOf", "includesPolicy", "hasRowRule", "hasColumnRule", "belongsToTable", "belongsToSchema"]


def _serialize_graph_node(node: Any) -> Dict[str, Any]:
    labels = list(node.labels)
    return {
        "key": node.element_id,
        "label": labels[0] if labels else "Node",
        "labels": labels,
        "properties": dict(node.items()),
    }


def _serialize_graph_relationship(rel: Any) -> Dict[str, Any]:
    return {
        "key": rel.element_id,
        "from": rel.start_node.element_id,
        "to": rel.end_node.element_id,
        "type": rel.type,
        "properties": dict(rel.items()),
    }


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _records_to_graph(rows: List[Any]) -> Dict[str, Any]:
    node_map: Dict[str, Dict[str, Any]] = {}
    links: Dict[str, Dict[str, Any]] = {}

    def visit(value: Any):
        if value is None:
            return
        if hasattr(value, "labels") and hasattr(value, "element_id"):
            node_map.setdefault(value.element_id, _serialize_graph_node(value))
            return
        if hasattr(value, "type") and hasattr(value, "element_id") and hasattr(value, "start_node"):
            node_map.setdefault(value.start_node.element_id, _serialize_graph_node(value.start_node))
            node_map.setdefault(value.end_node.element_id, _serialize_graph_node(value.end_node))
            links.setdefault(value.element_id, _serialize_graph_relationship(value))
            return
        if hasattr(value, "nodes") and hasattr(value, "relationships"):
            for n in value.nodes:
                visit(n)
            for r in value.relationships:
                visit(r)
            return
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if isinstance(value, dict):
            for item in value.values():
                visit(item)

    for row in rows:
        for value in row.values():
            visit(value)

    return {"nodes": list(node_map.values()), "links": list(links.values())}


def _records_to_table(rows: List[Any]) -> Dict[str, Any]:
    columns = list(rows[0].keys()) if rows else []
    data = []
    for row in rows:
        item = {}
        for column in columns:
            value = row[column]
            if isinstance(value, dict):
                item[column] = {k: _normalize_scalar(v) for k, v in value.items()}
            elif isinstance(value, list):
                item[column] = [_normalize_scalar(v) for v in value]
            else:
                item[column] = _normalize_scalar(value)
        data.append(item)
    return {"columns": columns, "rows": data}


def _is_graph_result(rows: List[Any]) -> bool:
    if not rows:
        return False
    for row in rows:
        for value in row.values():
            if hasattr(value, "labels") and hasattr(value, "element_id"):
                return True
            if hasattr(value, "type") and hasattr(value, "start_node"):
                return True
            if hasattr(value, "nodes") and hasattr(value, "relationships"):
                return True
            if isinstance(value, list) and any(hasattr(item, "element_id") for item in value):
                return True
    return False


def _cypher_schema_prompt() -> str:
    return (
        "You generate read-only Cypher for a Neo4j entitlement graph.\n"
        "Allowed labels: User, PolicyGroup, Policy, Schema, Table, Column.\n"
        "Allowed relationships: memberOf, includesPolicy, hasRowRule, hasColumnRule, belongsToTable, belongsToSchema.\n"
        "Important properties:\n"
        "- User.userId\n"
        "- PolicyGroup.policyGroupId, PolicyGroup.policyGroupName\n"
        "- Policy.policyId, Policy.policyName, Policy.definition\n"
        "- Schema.schemaId, Schema.schemaName\n"
        "- Table.tableId, Table.tableName\n"
        "- Column.columnId, Column.columnName\n"
        "Return strict JSON only: {\"cypher\":\"...\",\"result_mode\":\"graph\"|\"table\"}.\n"
        "Use result_mode=graph when returning nodes, relationships, or paths. Use result_mode=table for aggregations and scalar results.\n"
        "Use LIMIT 100 unless the question explicitly needs a smaller limit.\n"
        "Never generate CREATE, MERGE, SET, DELETE, REMOVE, DROP, CALL, LOAD CSV, or APOC.\n"
    )


def _fallback_chat_plan(question: str) -> Dict[str, str]:
    q = question.lower()
    if any(word in q for word in ["count", "how many", "number of"]):
        if "relationship" in q or "edge" in q:
            return {
                "cypher": "MATCH ()-[r]->() RETURN type(r) AS relationshipType, count(*) AS count ORDER BY count DESC",
                "result_mode": "table",
            }
        return {
            "cypher": (
                "MATCH (n) "
                "UNWIND labels(n) AS label "
                "WHERE label IN ['User','PolicyGroup','Policy','Schema','Table','Column'] "
                "RETURN label, count(*) AS count ORDER BY count DESC"
            ),
            "result_mode": "table",
        }
    if any(word in q for word in ["show", "graph", "relationship", "connected", "link"]):
        return {
            "cypher": (
                "MATCH (a)-[r]->(b) "
                "WHERE any(l IN labels(a) WHERE l IN ['User','PolicyGroup','Policy','Schema','Table','Column']) "
                "AND any(l IN labels(b) WHERE l IN ['User','PolicyGroup','Policy','Schema','Table','Column']) "
                "AND type(r) IN ['memberOf','includesPolicy','hasRowRule','hasColumnRule','belongsToTable','belongsToSchema'] "
                "RETURN a, r, b LIMIT 100"
            ),
            "result_mode": "graph",
        }
    text = re.sub(r"[^a-z0-9_ -]", " ", q).strip()
    if text:
        token = text.split()[0]
        return {
            "cypher": (
                "MATCH (n) "
                "WHERE any(l IN labels(n) WHERE l IN ['User','PolicyGroup','Policy','Schema','Table','Column']) "
                "AND any(v IN [value IN properties(n) | toLower(toString(value))] WHERE v CONTAINS $term) "
                "RETURN labels(n) AS labels, properties(n) AS properties LIMIT 50"
            ),
            "result_mode": "table",
        }
    return {
        "cypher": "MATCH (n) RETURN labels(n) AS labels, properties(n) AS properties LIMIT 25",
        "result_mode": "table",
    }


def _generate_chat_cypher(question: str) -> Dict[str, str]:
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
    except Exception:
        return _fallback_chat_plan(question)

    if not os.getenv("OPENAI_API_KEY"):
        return _fallback_chat_plan(question)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    msg = llm.invoke(
        [
            SystemMessage(content=_cypher_schema_prompt()),
            HumanMessage(content=question),
        ]
    )
    content = msg.content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        payload = json.loads(content)
        cypher = str(payload.get("cypher") or "").strip()
        result_mode = str(payload.get("result_mode") or "table").strip().lower()
        if not cypher:
            raise ValueError("Missing cypher")
        return {"cypher": cypher, "result_mode": "graph" if result_mode == "graph" else "table"}
    except Exception:
        return _fallback_chat_plan(question)


def _ensure_read_only_cypher(cypher: str):
    banned = ["create ", "merge ", "set ", "delete ", "detach ", "remove ", "drop ", "call ", "load csv", "apoc."]
    normalized = re.sub(r"\s+", " ", cypher.strip().lower())
    if any(token in normalized for token in banned):
        raise HTTPException(status_code=400, detail="Generated Cypher must be read-only")


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


@app.get("/api/dashboard")
def get_dashboard():
    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            entity_rows = session.run(
                """
                MATCH (n)
                UNWIND labels(n) AS label
                WITH label
                WHERE label IN $labels
                RETURN label AS entityType, count(*) AS count
                ORDER BY entityType
                """,
                labels=_known_labels(),
            )
            relationship_rows = session.run(
                """
                MATCH ()-[r]->()
                WHERE type(r) IN $rel_types
                RETURN type(r) AS relationshipType, count(*) AS count
                ORDER BY relationshipType
                """,
                rel_types=_known_rel_types(),
            )
            return {
                "entity_counts": [
                    {"entity_type": row["entityType"], "count": row["count"]}
                    for row in entity_rows
                ],
                "relationship_counts": [
                    {"relationship_type": row["relationshipType"], "count": row["count"]}
                    for row in relationship_rows
                ],
            }
    finally:
        driver.close()


@app.get("/api/search")
def search_entities(q: str):
    term = q.strip().lower()
    if not term:
        return []
    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            rows = session.run(
                """
                MATCH (n)
                WHERE any(l IN labels(n) WHERE l IN $labels)
                  AND any(k IN keys(properties(n)) WHERE toLower(toString(properties(n)[k])) CONTAINS $term)
                RETURN labels(n) AS labels, properties(n) AS properties
                LIMIT 50
                """,
                labels=_known_labels(),
                term=term,
            )
            results = []
            for row in rows:
                labels = row["labels"] or []
                properties = row["properties"] or {}
                results.append(
                    {
                        "label": labels[0] if labels else "Node",
                        "labels": labels,
                        "properties": properties,
                    }
                )
            return results
    finally:
        driver.close()


@app.get("/api/search/relationships")
def search_relationships(q: str):
    term = q.strip().lower()
    if not term:
        return []
    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            rows = session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE type(r) IN $rel_types
                  AND (
                    toLower(type(r)) CONTAINS $term OR
                    any(k IN keys(properties(r)) WHERE toLower(toString(properties(r)[k])) CONTAINS $term)
                  )
                RETURN
                  type(r) AS relationshipType,
                  properties(r) AS properties,
                  labels(a) AS fromLabels,
                  properties(a) AS fromProperties,
                  labels(b) AS toLabels,
                  properties(b) AS toProperties
                LIMIT 50
                """,
                rel_types=_known_rel_types(),
                term=term,
            )
            results = []
            for row in rows:
                results.append(
                    {
                        "type": row["relationshipType"],
                        "properties": row["properties"] or {},
                        "from": {
                            "label": (row["fromLabels"] or ["Node"])[0],
                            "labels": row["fromLabels"] or [],
                            "properties": row["fromProperties"] or {},
                        },
                        "to": {
                            "label": (row["toLabels"] or ["Node"])[0],
                            "labels": row["toLabels"] or [],
                            "properties": row["toProperties"] or {},
                        },
                    }
                )
            return results
    finally:
        driver.close()


@app.post("/api/chat-explorer")
def chat_explorer(req: ChatExplorerRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    plan = _generate_chat_cypher(question)
    cypher = plan["cypher"].strip()
    _ensure_read_only_cypher(cypher)

    params = {}
    if "$term" in cypher:
        params["term"] = question.strip().lower()

    driver, database = _neo4j_driver()
    try:
        with driver.session(database=database) as session:
            rows = list(session.run(cypher, **params))
    finally:
        driver.close()

    graph_like = _is_graph_result(rows)
    result_mode = "graph" if graph_like or (plan["result_mode"] == "graph" and not rows) else "table"
    payload: Dict[str, Any] = {
        "question": question,
        "cypher": cypher,
        "result_mode": result_mode,
        "row_count": len(rows),
    }
    if result_mode == "graph":
        payload["graph"] = _records_to_graph(rows)
    else:
        payload["table"] = _records_to_table(rows)
    return payload


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
