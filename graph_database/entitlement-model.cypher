MERGE (policy:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy'}) ON CREATE SET policy.rdfs__label='policy', policy.skos__definition='Encapsulates access logic combining row-level and column-level rules.', policy.note='Each policy must have a policy_id and policy_name; may include definition.';
MERGE (policyGroup:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy_group'}) ON CREATE SET policyGroup.rdfs__label='policy group', policyGroup.skos__definition='A collection of policies aligned to a persona function or role set.', policyGroup.note='Each policy group must have a policy_group_id and policy_group_name; may include definition.';
MERGE (columnA:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/column'}) ON CREATE SET columnA.rdfs__label='column', columnA.skos__definition='Represents a physical database column.';
MERGE (table:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/table'}) ON CREATE SET table.rdfs__label='table', table.skos__definition='Database table grouping columns within a schema.', table.note='Contains columns such as customer_email.';
MERGE (schema:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/schema'}) ON CREATE SET schema.rdfs__label='schema', schema.skos__definition='Database schema grouping tables within a database catalog.', schema.note='Schema for tables.';
MERGE (user:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/user'}) ON CREATE SET user.rdfs__label='user', user.skos__definition='Subject or principal entitled to policy groups.', user.note='Example user Alice with membership to a policy group.';
MERGE (dt_policy_id:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/policy_id'}) ON CREATE SET dt_policy_id.rdfs__label='policy id datatype', dt_policy_id.skos__definition='Datatype node for policy_id property.', dt_policy_id.xml__datatype='xsd:string', dt_policy_id.format='uuid';
MERGE (dt_policy_name:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/policy_name'}) ON CREATE SET dt_policy_name.rdfs__label='policy name datatype', dt_policy_name.skos__definition='Datatype node for policy_name property.', dt_policy_name.xml__datatype='xsd:string', dt_policy_name.format='text';
MERGE (dt_policy_def:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/policy_definition'}) ON CREATE SET dt_policy_def.rdfs__label='policy definition datatype', dt_policy_def.skos__definition='Datatype node for optional policy definition.', dt_policy_def.xml__datatype='xsd:string', dt_policy_def.format='text';
MERGE (dt_policy_group_id:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/policy_group_id'}) ON CREATE SET dt_policy_group_id.rdfs__label='policy group id datatype', dt_policy_group_id.skos__definition='Datatype node for policy_group_id property.', dt_policy_group_id.xml__datatype='xsd:string', dt_policy_group_id.format='uuid';
MERGE (dt_policy_group_name:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/policy_group_name'}) ON CREATE SET dt_policy_group_name.rdfs__label='policy group name datatype', dt_policy_group_name.skos__definition='Datatype node for policy_group_name property.', dt_policy_group_name.xml__datatype='xsd:string', dt_policy_group_name.format='text';
MERGE (dt_column_id:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/column_id'}) ON CREATE SET dt_column_id.rdfs__label='column id datatype', dt_column_id.skos__definition='Datatype node for column_id property.', dt_column_id.xml__datatype='xsd:string', dt_column_id.format='uuid';
MERGE (dt_column_name:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/column_name'}) ON CREATE SET dt_column_name.rdfs__label='column name datatype', dt_column_name.skos__definition='Datatype node for column_name property.', dt_column_name.xml__datatype='xsd:string', dt_column_name.format='text';
MERGE (dt_table_id:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/table_id'}) ON CREATE SET dt_table_id.rdfs__label='table id datatype', dt_table_id.skos__definition='Datatype node for table_id property.', dt_table_id.xml__datatype='xsd:string', dt_table_id.format='uuid';
MERGE (dt_table_name:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/table_name'}) ON CREATE SET dt_table_name.rdfs__label='table name datatype', dt_table_name.skos__definition='Datatype node for table_name property.', dt_table_name.xml__datatype='xsd:string', dt_table_name.format='text';
MERGE (dt_schema_id:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/schema_id'}) ON CREATE SET dt_schema_id.rdfs__label='schema id datatype', dt_schema_id.skos__definition='Datatype node for schema_id property.', dt_schema_id.xml__datatype='xsd:string', dt_schema_id.format='uuid';
MERGE (dt_schema_name:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/schema_name'}) ON CREATE SET dt_schema_name.rdfs__label='schema name datatype', dt_schema_name.skos__definition='Datatype node for schema_name property.', dt_schema_name.xml__datatype='xsd:string', dt_schema_name.format='text';
//hasRowRule
MATCH (policy:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy'}),
      (col:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/column'})
WITH policy, col
MERGE (policy)-[r:hasRowRule {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy/hasRowRule/customer_email',
                              rdfs__label:'has row rule',
                              skos__definition:'Policy includes row-level access condition that applies to a specific column.',
                              owl__minQualifiedCardinality:0, owl__maxQualifiedCardinality:9999}]
->(col);
MATCH (policy:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy'}), (col:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/column'}) WITH policy, col MERGE (policy)-[r:hasColumnRule {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy/hasColumnRule/account_balance', rdfs__label:'has column rule', skos__definition:'Policy includes column-level masking logic that applies to a specific column.', owl__minQualifiedCardinality:0, owl__maxQualifiedCardinality:9999}]->(col);
MATCH (pg:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy_group'}), (policy:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy'}) WITH pg, policy MERGE (pg)-[r:includesPolicy {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy_group/includesPolicy/policy', rdfs__label:'includes policy', skos__definition:'Policy group bundles policies.', owl__minQualifiedCardinality:0, owl__maxQualifiedCardinality:9999}]->(policy);
MATCH (user:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/user'}), (pg:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy_group'}) WITH user, pg MERGE (user)-[r:memberOf {uri:'http://upupedu.com/ontology/entitlement/tabular_data/user/alice/memberOf/policy_group', rdfs__label:'member of', skos__definition:'User inherits policies through group membership.', owl__minQualifiedCardinality:0, owl__maxQualifiedCardinality:9999}]->(pg);
// Relationship: column belongs to table
MATCH (c:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/column'})
MATCH (t:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/table'})
MERGE (c)-[r:belongsToTable {uri:'http://upupedu.com/ontology/entitlement/tabular_data/belongsToTable'}]->(t)
ON CREATE SET
  r.rdfs__label = 'belongs to table',
  r.skos__definition = 'A column is always contained in exactly one table.',
  r.owl__minQualifiedCardinality = 1,
  r.owl__maxQualifiedCardinality = 1;

// Relationship: table belongs to schema
MATCH (t:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/table'})
MATCH (s:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/schema'})
MERGE (t)-[r:belongsToSchema {uri:'http://upupedu.com/ontology/entitlement/tabular_data/belongsToSchema'}]->(s)
ON CREATE SET
  r.rdfs__label = 'belongs to schema',
  r.skos__definition = 'A table is always contained in exactly one schema.',
  r.owl__minQualifiedCardinality = 1,
  r.owl__maxQualifiedCardinality = 1;
MATCH (policy:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/policy_id'})
MERGE (policy)-[r:policyId {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy/policyId',
    rdfs__label:'policy id',
    skos__definition:'Links policy to its policy_id datatype.',
    owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1
}]->(dt);

MATCH (policy:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/policy_name'})
MERGE (policy)-[r:policyName {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy/policyName',
    rdfs__label:'policy name',
    skos__definition:'Links policy to its policy_name datatype.',
    owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1
}]->(dt);

MATCH (policy:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/policy_definition'})
MERGE (policy)-[r:definition {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy/definition',
    rdfs__label:'definition',
    skos__definition:'Optional textual definition for a policy.',
    owl__minQualifiedCardinality:0, owl__maxQualifiedCardinality:1
}]->(dt);

MATCH (pg:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy_group'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/policy_group_id'})
MERGE (pg)-[r:policyGroupId {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy_group/policyGroupId',
    rdfs__label:'policy group id',
    skos__definition:'Links policy group to its id datatype.',
    owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1
}]->(dt);

MATCH (pg:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy_group'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/policy_group_name'})
MERGE (pg)-[r:policyGroupName {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy_group/policyGroupName',
    rdfs__label:'policy group name',
    skos__definition:'Links policy group to its name datatype.',
    owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1
}]->(dt);

MATCH (col:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/column'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/column_id'})
MERGE (col)-[r:columnId {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/column/customer_email/columnId',
    rdfs__label:'column id',
    skos__definition:'Links column to its id datatype.',
    owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1
}]->(dt);

MATCH (col:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/column'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/column_name'})
MERGE (col)-[r:columnName {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/column/customer_email/columnName',
    rdfs__label:'column name',
    skos__definition:'Links column to its name datatype.',
    owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1
}]->(dt);

MATCH (t:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/table'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/table_id'})
MERGE (t)-[r:tableId {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/table/customer/tableId',
    rdfs__label:'table id',
    skos__definition:'Links table to its id datatype.',
    owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1
}]->(dt);

MATCH (t:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/table'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/table_name'})
MERGE (t)-[r:tableName {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/table/customer/tableName',
    rdfs__label:'table name',
    skos__definition:'Links table to its name datatype.',
    owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1
}]->(dt);

MATCH (s:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/schema'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/schema_id'})
MERGE (s)-[r:schemaId {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/schema/sales/schemaId',
    rdfs__label:'schema id',
    skos__definition:'Links schema to its id datatype.',
    owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1
}]->(dt);

MATCH (s:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/schema'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/schema_name'})
MERGE (s)-[r:schemaName {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/schema/sales/schemaName',
    rdfs__label:'schema name',
    skos__definition:'Links schema to its name datatype.',
    owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1
}]->(dt);

MATCH (u:owl__Class {uri:'http://upupedu.com/ontology/entitlement/tabular_data/user'}),
      (dt:rdfs__Datatype {uri:'http://upupedu.com/ontology/entitlement/tabular_data/datatype/user_id'})
MERGE (u)-[r:userId {
    uri:'http://upupedu.com/ontology/entitlement/tabular_data/user/alice/userId',
    rdfs__label:'user id',
    skos__definition:'Links user to its user_id datatype.',
    owl__minQualifiedCardinality:1, owl__maxQualifiedCardinality:1
}]->(dt);