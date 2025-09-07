// === Constraints ===
CREATE CONSTRAINT owl_uri IF NOT EXISTS
FOR (n:owl__Class) REQUIRE n.uri IS UNIQUE;

// === Classes (all nodes are :owl__Class) ===
MERGE (policy:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy',
  rdfs__label:'policy',
  skos__definition:'Logical policy that can bind row and column rules',
  policy_name:'Name of the policy.',
  definition:'Policy logic.'
});

MERGE (policyGroup:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/policy_group',
  rdfs__label:'policy group',
  skos__definition:'Bundle of policies representing a persona or role set',
  policy_group_name:'Name of the group/persona.',
  definition: 'Group scope.'
});

MERGE (rowFilterRule:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/row_filter_rule',
  rdfs__label:'row filter rule',
  skos__definition:'Row level predicate rule defined on a table column',
  filter_operator:'Predicate operator EQUAL/NOT_EQUAL/IN/LIKE/BETWEEN.',
  match_value:'Value/pattern/list used by operator.'
});


MERGE (columnMaskRule:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/column_mask_rule',
  rdfs__label:'column mask rule',
  skos__definition:'Column level masking or transformation rule',
  mask_algorithm:'Masking algorithm.'
});


MERGE (columnCls:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/column',
  rdfs__label:'column',
  skos__definition:'Relational column identified by schema table and column name',
  schema_name:'schema/owner of target table.',
  table_name: 'Target table name of the policy.',
  column_name:'target column of the policy.'

});

MERGE (userCls:owl__Class {
  uri:'http://upupedu.com/ontology/entitlement/tabular_data/user',
  rdfs__label:'user',
  skos__definition:'Subject or principal that can be entitled to a policy group',
  user_id: "Unique user Identity"
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


// user → policyGroup
MERGE (userCls)-[r6:memberOf]->(policyGroup)
  ON CREATE SET r6.skos__definition = "User is a member of a policy group and inherits its policies",
  r6.status = "Grant status: ACTIVE, REVOKED, PENDING.",r6.granted_at = "Date/time the entitlement was granted.", r6.revoked_at = "Date/time the entitlement was revoked."
;

// policyGroup → policy
MERGE (policyGroup)-[r7:includesPolicy]->(policy)
  ON CREATE SET r7.skos__definition = "Policy group includes one or more policies";