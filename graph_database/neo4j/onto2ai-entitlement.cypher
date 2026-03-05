// Ontology: onto2ai-entitlement
// Purpose: Policy-driven data protection for JDBC-connected relational databases.

MERGE (onto:owl__Ontology {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement'})
ON CREATE SET
  onto.rdfs__label = 'onto2ai-entitlement',
  onto.skos__definition = 'Ontology for row-level and column-level entitlement enforcement across JDBC-accessible relational databases.',
  onto.version = '1.0.0';

// ===== Classes =====
MERGE (subject:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Subject'})
  ON CREATE SET subject.rdfs__label='subject', subject.skos__definition='Principal that receives entitlements.';
MERGE (user:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#User'})
  ON CREATE SET user.rdfs__label='user', user.skos__definition='Human user principal for policy evaluation.';
MERGE (policyGroup:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#PolicyGroup'})
  ON CREATE SET policyGroup.rdfs__label='policy group', policyGroup.skos__definition='Collection of policies mapped to a persona, role, or function.';
MERGE (policy:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Policy'})
  ON CREATE SET policy.rdfs__label='policy', policy.skos__definition='Bundle of row-filter and/or column-mask rules.';
MERGE (rowRule:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#RowFilterRule'})
  ON CREATE SET rowRule.rdfs__label='row filter rule', rowRule.skos__definition='Rule that restricts row visibility using predicates.';
MERGE (maskRule:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#ColumnMaskRule'})
  ON CREATE SET maskRule.rdfs__label='column mask rule', maskRule.skos__definition='Rule that transforms or redacts sensitive column values.';
MERGE (schema:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Schema'})
  ON CREATE SET schema.rdfs__label='schema', schema.skos__definition='Relational schema/container for tables.';
MERGE (table:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Table'})
  ON CREATE SET table.rdfs__label='table', table.skos__definition='Relational table containing columns.';
MERGE (columnA:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Column'})
  ON CREATE SET columnA.rdfs__label='column', columnA.skos__definition='Relational column protected by entitlement rules.';
MERGE (rdbms:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#RelationalDatabase'})
  ON CREATE SET rdbms.rdfs__label='relational database', rdbms.skos__definition='JDBC-connectable relational database platform.';
MERGE (jdbc:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#JdbcConnectionProfile'})
  ON CREATE SET jdbc.rdfs__label='jdbc connection profile', jdbc.skos__definition='JDBC endpoint and driver metadata for a target database.';

// ===== Class hierarchy =====
MATCH (subject:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Subject'}),
      (user:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#User'})
MERGE (user)-[:rdfs__subClassOf {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#User/subClassOf/Subject'}]->(subject);

// ===== Datatype nodes =====
MERGE (dt_subject_id:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/subject_id'})
  ON CREATE SET dt_subject_id.rdfs__label='subject id datatype', dt_subject_id.xml__datatype='xsd:string';
MERGE (dt_policy_id:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/policy_id'})
  ON CREATE SET dt_policy_id.rdfs__label='policy id datatype', dt_policy_id.xml__datatype='xsd:string';
MERGE (dt_policy_name:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/policy_name'})
  ON CREATE SET dt_policy_name.rdfs__label='policy name datatype', dt_policy_name.xml__datatype='xsd:string';
MERGE (dt_policy_def:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/policy_definition'})
  ON CREATE SET dt_policy_def.rdfs__label='policy definition datatype', dt_policy_def.xml__datatype='xsd:string';
MERGE (dt_group_id:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/policy_group_id'})
  ON CREATE SET dt_group_id.rdfs__label='policy group id datatype', dt_group_id.xml__datatype='xsd:string';
MERGE (dt_group_name:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/policy_group_name'})
  ON CREATE SET dt_group_name.rdfs__label='policy group name datatype', dt_group_name.xml__datatype='xsd:string';
MERGE (dt_rule_expr:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/rule_expression'})
  ON CREATE SET dt_rule_expr.rdfs__label='rule expression datatype', dt_rule_expr.xml__datatype='xsd:string';
MERGE (dt_rule_type:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/rule_type'})
  ON CREATE SET dt_rule_type.rdfs__label='rule type datatype', dt_rule_type.xml__datatype='xsd:string';
MERGE (dt_schema_name:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/schema_name'})
  ON CREATE SET dt_schema_name.rdfs__label='schema name datatype', dt_schema_name.xml__datatype='xsd:string';
MERGE (dt_table_name:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/table_name'})
  ON CREATE SET dt_table_name.rdfs__label='table name datatype', dt_table_name.xml__datatype='xsd:string';
MERGE (dt_column_name:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/column_name'})
  ON CREATE SET dt_column_name.rdfs__label='column name datatype', dt_column_name.xml__datatype='xsd:string';
MERGE (dt_db_vendor:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/database_vendor'})
  ON CREATE SET dt_db_vendor.rdfs__label='database vendor datatype', dt_db_vendor.xml__datatype='xsd:string';
MERGE (dt_jdbc_url:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/jdbc_url'})
  ON CREATE SET dt_jdbc_url.rdfs__label='jdbc url datatype', dt_jdbc_url.xml__datatype='xsd:string';
MERGE (dt_jdbc_driver:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/jdbc_driver'})
  ON CREATE SET dt_jdbc_driver.rdfs__label='jdbc driver datatype', dt_jdbc_driver.xml__datatype='xsd:string';

// ===== Object properties =====
MATCH (u:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#User'}),
      (pg:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#PolicyGroup'})
MERGE (u)-[:memberOf {
  uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#memberOf',
  rdfs__label:'member of',
  skos__definition:'User inherits policies via policy group membership.',
  owl__minQualifiedCardinality:0,
  owl__maxQualifiedCardinality:9999
}]->(pg);

MATCH (pg:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#PolicyGroup'}),
      (p:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Policy'})
MERGE (pg)-[:includesPolicy {
  uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#includesPolicy',
  rdfs__label:'includes policy',
  skos__definition:'Policy group bundles one or more policies.',
  owl__minQualifiedCardinality:0,
  owl__maxQualifiedCardinality:9999
}]->(p);

MATCH (p:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Policy'}),
      (rr:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#RowFilterRule'})
MERGE (p)-[:hasRowRule {
  uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#hasRowRule',
  rdfs__label:'has row rule',
  skos__definition:'Policy contains row-level filtering rules.',
  owl__minQualifiedCardinality:0,
  owl__maxQualifiedCardinality:9999
}]->(rr);

MATCH (p:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Policy'}),
      (mr:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#ColumnMaskRule'})
MERGE (p)-[:hasColumnRule {
  uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#hasColumnRule',
  rdfs__label:'has column rule',
  skos__definition:'Policy contains column masking rules.',
  owl__minQualifiedCardinality:0,
  owl__maxQualifiedCardinality:9999
}]->(mr);

MATCH (rr:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#RowFilterRule'}),
      (c:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Column'})
MERGE (rr)-[:targetsColumn {
  uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#targetsColumnFromRowRule',
  rdfs__label:'targets column',
  skos__definition:'Row-filter rule targets a specific column context.'
}]->(c);

MATCH (mr:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#ColumnMaskRule'}),
      (c:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Column'})
MERGE (mr)-[:targetsColumn {
  uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#targetsColumnFromMaskRule',
  rdfs__label:'targets column',
  skos__definition:'Column-mask rule targets a specific column.'
}]->(c);

MATCH (c:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Column'}),
      (t:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Table'})
MERGE (c)-[:belongsToTable {
  uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#belongsToTable',
  rdfs__label:'belongs to table',
  skos__definition:'A column belongs to exactly one table.',
  owl__minQualifiedCardinality:1,
  owl__maxQualifiedCardinality:1
}]->(t);

MATCH (t:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Table'}),
      (s:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Schema'})
MERGE (t)-[:belongsToSchema {
  uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#belongsToSchema',
  rdfs__label:'belongs to schema',
  skos__definition:'A table belongs to exactly one schema.',
  owl__minQualifiedCardinality:1,
  owl__maxQualifiedCardinality:1
}]->(s);

MATCH (s:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Schema'}),
      (db:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#RelationalDatabase'})
MERGE (s)-[:partOfDatabase {
  uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#partOfDatabase',
  rdfs__label:'part of database',
  skos__definition:'Schema belongs to a relational database.'
}]->(db);

MATCH (conn:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#JdbcConnectionProfile'}),
      (db:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#RelationalDatabase'})
MERGE (conn)-[:connectsTo {
  uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#connectsTo',
  rdfs__label:'connects to',
  skos__definition:'JDBC profile connects to a target relational database.'
}]->(db);

// ===== Datatype properties =====
MATCH (s:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Subject'}),
      (dt:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/subject_id'})
MERGE (s)-[:subjectId {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#subjectId', rdfs__label:'subject id', owl__minQualifiedCardinality:0, owl__maxQualifiedCardinality:1}]->(dt);

MATCH (u:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#User'}),
      (dt:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/subject_id'})
MERGE (u)-[:userId {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#userId', rdfs__label:'user id', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(dt);

MATCH (pg:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#PolicyGroup'}),
      (id:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/policy_group_id'}),
      (name:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/policy_group_name'})
MERGE (pg)-[:policyGroupId {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#policyGroupId', rdfs__label:'policy group id', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(id)
MERGE (pg)-[:policyGroupName {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#policyGroupName', rdfs__label:'policy group name', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(name);

MATCH (p:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Policy'}),
      (id:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/policy_id'}),
      (name:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/policy_name'}),
      (defn:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/policy_definition'})
MERGE (p)-[:policyId {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#policyId', rdfs__label:'policy id', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(id)
MERGE (p)-[:policyName {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#policyName', rdfs__label:'policy name', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(name)
MERGE (p)-[:definition {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#definition', rdfs__label:'definition', owl__minQualifiedCardinality:0, owl__maxQualifiedCardinality:1}]->(defn);

MATCH (rr:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#RowFilterRule'}),
      (expr:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/rule_expression'}),
      (typ:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/rule_type'})
MERGE (rr)-[:ruleExpression {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#ruleExpression', rdfs__label:'rule expression', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(expr)
MERGE (rr)-[:ruleType {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#ruleType', rdfs__label:'rule type', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(typ);

MATCH (mr:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#ColumnMaskRule'}),
      (expr:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/rule_expression'}),
      (typ:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/rule_type'})
MERGE (mr)-[:ruleExpression {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#ruleExpression', rdfs__label:'rule expression', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(expr)
MERGE (mr)-[:ruleType {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#ruleType', rdfs__label:'rule type', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(typ);

MATCH (s:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Schema'}),
      (dt:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/schema_name'})
MERGE (s)-[:schemaName {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#schemaName', rdfs__label:'schema name', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(dt);

MATCH (t:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Table'}),
      (dt:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/table_name'})
MERGE (t)-[:tableName {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#tableName', rdfs__label:'table name', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(dt);

MATCH (c:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#Column'}),
      (dt:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/column_name'})
MERGE (c)-[:columnName {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#columnName', rdfs__label:'column name', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(dt);

MATCH (db:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#RelationalDatabase'}),
      (dt:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/database_vendor'})
MERGE (db)-[:databaseVendor {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#databaseVendor', rdfs__label:'database vendor', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(dt);

MATCH (j:owl__Class {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#JdbcConnectionProfile'}),
      (url:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/jdbc_url'}),
      (drv:rdfs__Datatype {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement/datatype/jdbc_driver'})
MERGE (j)-[:jdbcUrl {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#jdbcUrl', rdfs__label:'jdbc url', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(url)
MERGE (j)-[:jdbcDriver {uri:'http://www.onto2ai-toolset.com/ontology/entitlement/Onto2AIEntitlement#jdbcDriver', rdfs__label:'jdbc driver', owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1}]->(drv);
