UNWIND $rows AS r
MERGE (p:Policy {policyId: toInteger(r.policy_id)})
  ON CREATE SET p.policyName = r.policy_name,
                p.policyType = coalesce(r.policy_type,'HYBRID'),
                p.definition = r.definition
  ON MATCH  SET p.policyName = r.policy_name,
                p.policyType = coalesce(r.policy_type,'HYBRID'),
                p.definition = r.definition;

UNWIND $rows AS r
MERGE (g:PolicyGroup {policyGroupId: toInteger(r.policy_group_id)})
  ON CREATE SET g.policyGroupName = r.policy_group_name,
                g.groupType = coalesce(r.group_type,'PERSONA'),
                g.definition = r.definition
  ON MATCH  SET g.policyGroupName = r.policy_group_name,
                g.groupType = coalesce(r.group_type,'PERSONA'),
                g.definition = r.definition;
UNWIND $rows AS r
MERGE (t:Table {schemaName:r.schema_name, tableName:r.table_name});

UNWIND $rows AS r
MERGE (c:Column {schemaName:r.schema_name, tableName:r.table_name, columnName:r.column_name})
MERGE (t:Table {schemaName:r.schema_name, tableName:r.table_name})
MERGE (c)-[:inTable]->(t);

UNWIND $rows AS r
MERGE (rr:RowFilterRule {rowFilterRuleId: toInteger(r.row_filter_rule_id)})
  ON CREATE SET rr.schemaName = r.schema_name,
                rr.tableName  = r.table_name,
                rr.columnName = r.column_name,
                rr.matchValue = r.match_value,
                rr.filterOperator = coalesce(r.filter_operator,'EQUAL'),
                rr.description = r.description
  ON MATCH  SET rr.matchValue = r.match_value,
                rr.filterOperator = coalesce(r.filter_operator,'EQUAL'),
                rr.description = r.description
MERGE (c:Column {schemaName:r.schema_name, tableName:r.table_name, columnName:r.column_name})
MERGE (rr)-[:targetsColumn]->(c);

UNWIND $rows AS r
MERGE (mr:ColumnMaskRule {columnMaskRuleId: toInteger(r.column_mask_rule_id)})
  ON CREATE SET mr.schemaName = r.schema_name,
                mr.tableName  = r.table_name,
                mr.columnName = r.column_name,
                mr.maskAlgorithm = coalesce(r.mask_algorithm,'LAST_4_DIGIT'),
                mr.description = r.description
  ON MATCH  SET mr.maskAlgorithm = coalesce(r.mask_algorithm,'LAST_4_DIGIT'),
                mr.description = r.description
MERGE (c:Column {schemaName:r.schema_name, tableName:r.table_name, columnName:r.column_name})
MERGE (mr)-[:targetsColumn]->(c);

// policy_row_rule (row rules in a policy)
UNWIND $rows AS r
MATCH (p:Policy {policyId: toInteger(r.policy_id)})
MATCH (rr:RowFilterRule {rowFilterRuleId: toInteger(r.row_filter_rule_id)})
MERGE (p)-[rel:hasRowRule]->(rr)
  ON CREATE SET rel.status = coalesce(r.status,'ACTIVE')
  ON MATCH  SET rel.status = coalesce(r.status,'ACTIVE');

// policy_column_rule (column rules in a policy)
UNWIND $rows AS r
MATCH (p:Policy {policyId: toInteger(r.policy_id)})
MATCH (mr:ColumnMaskRule {columnMaskRuleId: toInteger(r.column_mask_rule_id)})
MERGE (p)-[rel:hasColumnRule]->(mr)
  ON CREATE SET rel.status = coalesce(r.status,'ACTIVE')
  ON MATCH  SET rel.status = coalesce(r.status,'ACTIVE');

UNWIND $rows AS r
MERGE (u:User {userId: r.user_id})
MERGE (g:PolicyGroup {policyGroupId: toInteger(r.policy_group_id)})
MERGE (u)-[m:memberOf]->(g)
  ON CREATE SET m.status     = coalesce(r.status,'ACTIVE'),
                m.grantedAt  = r.granted_at,
                m.revokedAt  = r.revoked_at
  ON MATCH  SET m.status     = coalesce(r.status,'ACTIVE'),
                m.grantedAt  = coalesce(m.grantedAt, r.granted_at),
                m.revokedAt  = coalesce(r.revoked_at, m.revokedAt);