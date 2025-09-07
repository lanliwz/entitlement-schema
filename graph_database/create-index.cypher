// === Identity / keys ===
CREATE CONSTRAINT policy_id IF NOT EXISTS
FOR (n:Policy) REQUIRE n.policyId IS UNIQUE;

CREATE CONSTRAINT policy_name IF NOT EXISTS
FOR (n:Policy) REQUIRE n.policyName IS UNIQUE;

CREATE CONSTRAINT policy_group_id IF NOT EXISTS
FOR (n:PolicyGroup) REQUIRE n.policyGroupId IS UNIQUE;

CREATE CONSTRAINT policy_group_name IF NOT EXISTS
FOR (n:PolicyGroup) REQUIRE n.policyGroupName IS UNIQUE;

CREATE CONSTRAINT row_filter_rule_id IF NOT EXISTS
FOR (n:RowFilterRule) REQUIRE n.rowFilterRuleId IS UNIQUE;

CREATE CONSTRAINT column_mask_rule_id IF NOT EXISTS
FOR (n:ColumnMaskRule) REQUIRE n.columnMaskRuleId IS UNIQUE;

// Tables and columns derive uniqueness from natural keys
CREATE CONSTRAINT table_key IF NOT EXISTS
FOR (t:Table) REQUIRE (t.schemaName, t.tableName) IS NODE KEY;

CREATE CONSTRAINT column_key IF NOT EXISTS
FOR (c:Column) REQUIRE (c.schemaName, c.tableName, c.columnName) IS NODE KEY;

CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.userId IS UNIQUE;

// Helpful lookup indexes
CREATE INDEX policy_type_idx IF NOT EXISTS FOR (n:Policy) ON (n.policyType);
CREATE INDEX group_type_idx  IF NOT EXISTS FOR (n:PolicyGroup) ON (n.groupType);
CREATE INDEX rule_op_idx     IF NOT EXISTS FOR (n:RowFilterRule) ON (n.filterOperator);
CREATE INDEX mask_algo_idx   IF NOT EXISTS FOR (n:ColumnMaskRule) ON (n.maskAlgorithm);