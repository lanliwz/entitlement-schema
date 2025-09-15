// === Identity / keys ===
CREATE CONSTRAINT policy_id IF NOT EXISTS
FOR (n:Policy) REQUIRE n.policyId IS UNIQUE;

CREATE CONSTRAINT policy_name IF NOT EXISTS
FOR (n:Policy) REQUIRE n.policyName IS UNIQUE;

CREATE CONSTRAINT policy_group_id IF NOT EXISTS
FOR (n:PolicyGroup) REQUIRE n.policyGroupId IS UNIQUE;

CREATE CONSTRAINT policy_group_name IF NOT EXISTS
FOR (n:PolicyGroup) REQUIRE n.policyGroupName IS UNIQUE;

CREATE CONSTRAINT table_key IF NOT EXISTS
FOR (t:Table) REQUIRE t.tableId IS UNIQUE;

CREATE CONSTRAINT column_key IF NOT EXISTS
FOR (c:Column) REQUIRE c.columnId IS UNIQUE;

CREATE CONSTRAINT schema_key IF NOT EXISTS
FOR (c:Schema) REQUIRE c.schemaId IS UNIQUE;

CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.userId IS UNIQUE;

