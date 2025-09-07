// === Constraints ===
CREATE CONSTRAINT owl_uri IF NOT EXISTS
FOR (n:owl__Class) REQUIRE n.uri IS UNIQUE;

// === Classes (all nodes are :owl__Class) ===
MERGE (policy:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy',
  rdfs__label:'policy',
  skos__definition:'Logical policy that can bind row and column rules'
});

MERGE (policyGroup:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy_group',
  rdfs__label:'policy group',
  skos__definition:'Bundle of policies representing a persona or role set'
});

MERGE (rowFilterRule:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/row_filter_rule',
  rdfs__label:'row filter rule',
  skos__definition:'Row level predicate rule defined on a table column'
});


MERGE (columnMaskRule:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/column_mask_rule',
  rdfs__label:'column mask rule',
  skos__definition:'Column level masking or transformation rule'
});

MERGE (tableCls:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/table',
  rdfs__label:'table',
  skos__definition:'Relational table identified by schema and name'
});

MERGE (columnCls:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/column',
  rdfs__label:'column',
  skos__definition:'Relational column identified by schema table and column name'
});

MERGE (userCls:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/user',
  rdfs__label:'user',
  skos__definition:'Subject or principal that can be entitled to a policy group'
});

// === Class-to-class schema relationships (meta edges) ===
// policy → rowFilterRule
MERGE (policy)-[r1:hasRowRule]->(rowFilterRule)
  ON CREATE SET r1.skos__definition = "Policy includes a row filter rule that restricts rows in a table";

// policy → columnMaskRule
MERGE (policy)-[r2:hasColumnRule]->(columnMaskRule)
  ON CREATE SET r2.skos__definition = "Policy includes a column mask rule that transforms or hides column values";

// rowFilterRule → column
MERGE (rowFilterRule)-[r3:targetsColumn]->(columnCls)
  ON CREATE SET r3.skos__definition = "Row filter rule applies to a specific column";

// columnMaskRule → column
MERGE (columnMaskRule)-[r4:targetsColumn]->(columnCls)
  ON CREATE SET r4.skos__definition = "Column mask rule applies to a specific column";

// column → table
MERGE (columnCls)-[r5:inTable]->(tableCls)
  ON CREATE SET r5.skos__definition = "Column belongs to a table";

// user → policyGroup
MERGE (userCls)-[r6:memberOf]->(policyGroup)
  ON CREATE SET r6.skos__definition = "User is a member of a policy group and inherits its policies";

// policyGroup → policy
MERGE (policyGroup)-[r7:includesPolicy]->(policy)
  ON CREATE SET r7.skos__definition = "Policy group includes one or more policies";