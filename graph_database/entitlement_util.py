import os

from neo4j import GraphDatabase
from typing import List, Dict, Any

neo4j_bolt_url = os.getenv("Neo4jFinDBUrl")
username = os.getenv("Neo4jFinDBUserName")
password = os.getenv("Neo4jFinDBPassword")

# 1. Create driver connection to Neo4j server
# Adjust host/port and credentials
driver = GraphDatabase.driver(
    neo4j_bolt_url,
    auth=(username, password),
    database='entitlement'
)

class EntitlementRepository:
    def __init__(self, driver):
        self.driver = driver

    def close(self):
        self.driver.close()

    def fetch_entitlements(self, user_id: str, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Fetch all entitlements (row rules and column mask rules) for a given user on a table within a schema.
        """
        query = """
        MATCH (u:User {userId: $userId})-[:memberOf]->(pg:PolicyGroup)-[:includesPolicy]->(p:Policy)
        MATCH (t:Table {tableName: $tableName})-[:belongsToSchema]->(s:Schema {schemaName: $schemaName})
        MATCH (c:Column)-[:belongsToTable]->(t)
        MATCH (p)-[r:hasRowRule|hasColumnRule]->(c)
        RETURN DISTINCT
            c.columnName AS columnName,
            p.definition  AS policyDefinition,
            CASE type(r)
                WHEN 'hasRowRule'    THEN 'ROW'
                WHEN 'hasColumnRule' THEN 'MASK'
            END AS ruleType
        ORDER BY columnName, ruleType
        """

        with self.driver.session() as session:
            results = session.run(
                query,
                userId=user_id,
                schemaName=schema_name,
                tableName=table_name
            )
            return [dict(r) for r in results]

    def add_mask_policy(
        self,
        schema_id: str, schema_name: str,
        table_id: str, table_name: str,
        column_id: str, column_name: str,
        policy_id: str, policy_name: str, definition: str,
        policy_group_id: str = None, policy_group_name: str = None
    ) -> Dict[str, Any]:
        """
        Add (or ensure) a mask policy for a column. Creates schema, table, column if missing.
        Optionally attaches the policy into a policy group.
        """
        cypher_core = """
        MERGE (s:Schema {schemaId: $schemaId})
          ON CREATE SET s.schemaName = $schemaName
        MERGE (t:Table {tableId: $tableId})
          ON CREATE SET t.tableName = $tableName
        MERGE (t)-[:belongsToSchema]->(s)
        MERGE (c:Column {columnId: $columnId})
          ON CREATE SET c.columnName = $columnName
        MERGE (c)-[:belongsToTable]->(t)
        MERGE (p:Policy {policyId: $policyId})
          ON CREATE SET p.policyName = $policyName,
                        p.definition = $definition
        MERGE (p)-[:hasColumnRule]->(c)
        RETURN
          p.policyId      AS policyId,
          p.policyName    AS policyName,
          p.definition    AS policyDefinition,
          s.schemaId      AS schemaId,
          s.schemaName    AS schemaName,
          t.tableId       AS tableId,
          t.tableName     AS tableName,
          c.columnId      AS columnId,
          c.columnName    AS columnName
        """
        cypher_group = """
        MERGE (pg:PolicyGroup {policyGroupId: $policyGroupId})
          ON CREATE SET pg.policyGroupName = $policyGroupName
        WITH pg
        MATCH (p:Policy {policyId: $policyId})
        MERGE (pg)-[:includesPolicy]->(p)
        RETURN pg.policyGroupId AS policyGroupId, pg.policyGroupName AS policyGroupName
        """

        with self.driver.session() as session:
            record = session.run(
                cypher_core,
                schemaId=schema_id,
                schemaName=schema_name,
                tableId=table_id,
                tableName=table_name,
                columnId=column_id,
                columnName=column_name,
                policyId=policy_id,
                policyName=policy_name,
                definition=definition
            ).single()

            result = dict(record) if record else {}

            if policy_group_id and policy_group_name:
                pg_rec = session.run(
                    cypher_group,
                    policyGroupId=policy_group_id,
                    policyGroupName=policy_group_name,
                    policyId=policy_id
                ).single()
                if pg_rec:
                    result.update(dict(pg_rec))

            return result
    # ---------------------------
    # Add user to policy group
    # ---------------------------
    def add_user_to_policy_group(
        self,
        user_id: str,
        policy_group_id: str,
        policy_group_name: str
    ) -> Dict[str, Any]:
        """
        Ensure the user and policy group exist, then attach the membership relation.
        """
        cypher = """
        MERGE (u:User {userId: $userId})
        MERGE (pg:PolicyGroup {policyGroupId: $policyGroupId})
          ON CREATE SET pg.policyGroupName = $policyGroupName
        MERGE (u)-[:memberOf]->(pg)
        RETURN u.userId AS userId,
               pg.policyGroupId AS policyGroupId,
               pg.policyGroupName AS policyGroupName
        """
        with self.driver.session() as session:
            rec = session.run(
                cypher,
                userId=user_id,
                policyGroupId=policy_group_id,
                policyGroupName=policy_group_name
            ).single()
            return dict(rec) if rec else {}
    # ---------------------------
    # Add policy to policy group
    # ---------------------------
    def add_policy_to_group(
        self,
        policy_id: str,
        policy_group_id: str,
        policy_group_name: str,
        policy_name: str | None = None,
        definition: str | None = None,
    ) -> dict:
        """
        Attach a Policy to a PolicyGroup.
        If policy_name/definition are provided, the Policy will be MERGE'd (created if missing).
        If not provided, the Policy must already exist (MATCH).
        """
        # Case A: Create-or-attach (MERGE policy)
        if policy_name is not None:
            cypher = """
            MERGE (pg:PolicyGroup {policyGroupId: $policyGroupId})
              ON CREATE SET pg.policyGroupName = $policyGroupName
            MERGE (p:Policy {policyId: $policyId})
              ON CREATE SET p.policyName = $policyName,
                            p.definition = $definition
            MERGE (pg)-[:includesPolicy]->(p)
            RETURN pg.policyGroupId   AS policyGroupId,
                   pg.policyGroupName AS policyGroupName,
                   p.policyId         AS policyId,
                   p.policyName       AS policyName,
                   p.definition       AS policyDefinition
            """
            params = {
                "policyGroupId": policy_group_id,
                "policyGroupName": policy_group_name,
                "policyId": policy_id,
                "policyName": policy_name,
                "definition": definition,
            }
        else:
            # Case B: Attach existing policy (MATCH policy)
            cypher = """
            MERGE (pg:PolicyGroup {policyGroupId: $policyGroupId})
              ON CREATE SET pg.policyGroupName = $policyGroupName
            WITH pg
            MATCH (p:Policy {policyId: $policyId})
            MERGE (pg)-[:includesPolicy]->(p)
            RETURN pg.policyGroupId   AS policyGroupId,
                   pg.policyGroupName AS policyGroupName,
                   p.policyId         AS policyId,
                   p.policyName       AS policyName,
                   p.definition       AS policyDefinition
            """
            params = {
                "policyGroupId": policy_group_id,
                "policyGroupName": policy_group_name,
                "policyId": policy_id,
            }

        with self.driver.session() as session:
            rec = session.run(cypher, **params).single()
            # If user tried to MATCH a non-existent policy, rec will be None
            return dict(rec) if rec else {}

    # ---------------------------
    # Add row policy
    # ---------------------------
    def add_row_policy(
        self,
        schema_id: str, schema_name: str,
        table_id: str, table_name: str,
        column_id: str, column_name: str,
        policy_id: str, policy_name: str, definition: str,
        policy_group_id: str = None, policy_group_name: str = None
    ) -> dict:
        """
        Add (or ensure) a row-level policy for a column.
        Creates schema, table, and column if they do not exist.
        Optionally links the policy to a policy group.
        """
        cypher_core = """
        MERGE (s:Schema {schemaId: $schemaId})
          ON CREATE SET s.schemaName = $schemaName
        MERGE (t:Table {tableId: $tableId})
          ON CREATE SET t.tableName = $tableName
        MERGE (t)-[:belongsToSchema]->(s)
        MERGE (c:Column {columnId: $columnId})
          ON CREATE SET c.columnName = $columnName
        MERGE (c)-[:belongsToTable]->(t)
        MERGE (p:Policy {policyId: $policyId})
          ON CREATE SET p.policyName = $policyName,
                        p.definition = $definition
        MERGE (p)-[:hasRowRule]->(c)
        RETURN
          p.policyId      AS policyId,
          p.policyName    AS policyName,
          p.definition    AS policyDefinition,
          s.schemaId      AS schemaId,
          s.schemaName    AS schemaName,
          t.tableId       AS tableId,
          t.tableName     AS tableName,
          c.columnId      AS columnId,
          c.columnName    AS columnName
        """
        cypher_group = """
        MERGE (pg:PolicyGroup {policyGroupId: $policyGroupId})
          ON CREATE SET pg.policyGroupName = $policyGroupName
        WITH pg
        MATCH (p:Policy {policyId: $policyId})
        MERGE (pg)-[:includesPolicy]->(p)
        RETURN pg.policyGroupId AS policyGroupId, pg.policyGroupName AS policyGroupName
        """

        with self.driver.session() as session:
            record = session.run(
                cypher_core,
                schemaId=schema_id,
                schemaName=schema_name,
                tableId=table_id,
                tableName=table_name,
                columnId=column_id,
                columnName=column_name,
                policyId=policy_id,
                policyName=policy_name,
                definition=definition
            ).single()

            result = dict(record) if record else {}

            if policy_group_id and policy_group_name:
                pg_rec = session.run(
                    cypher_group,
                    policyGroupId=policy_group_id,
                    policyGroupName=policy_group_name,
                    policyId=policy_id
                ).single()
                if pg_rec:
                    result.update(dict(pg_rec))

            return result
