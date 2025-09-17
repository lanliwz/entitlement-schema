from pydantic import BaseModel, Field
from typing import Optional, Dict, List

# ------------------- OpenAI Prompt -------------------
# create pydantic class, annotation properties as comment, \n
# relationship created as variable with type of the corresponding class



# ------------------- Core Node Classes -------------------

# rdfs__label: schema
# skos__definition: Database schema grouping tables within a database catalog.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/schema
# note: Schema for tables.
class Schema(BaseModel):
    schema_id: str = Field(..., description="Unique identifier for the schema")
    schema_name: str = Field(..., description="Name of the schema")


# rdfs__label: table
# skos__definition: Database table grouping columns within a schema.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/table
# note: Contains columns such as customer_email.
class Table(BaseModel):
    table_id: str = Field(..., description="Unique identifier for the table")
    table_name: str = Field(..., description="Name of the table")

    # Relationship: (:Table)-[:belongsToSchema]->(:Schema)
    # rdfs__label: belongs to schema
    # skos__definition: A table is always contained in exactly one schema.
    belongsToSchema: Optional[Schema] = Field(
        None, description="Target Schema this Table belongs to (cardinality 1)."
    )


# rdfs__label: column
# skos__definition: Represents a physical database column.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/column
class Column(BaseModel):
    column_id: str = Field(..., description="Unique identifier for the column")
    column_name: str = Field(..., description="Name of the column")

    # Relationship: (:Column)-[:belongsToTable]->(:Table)
    # rdfs__label: belongs to table
    # skos__definition: A column is always contained in exactly one table.
    belongsToTable: Optional[Table] = Field(
        None, description="Target Table this Column belongs to (cardinality 1)."
    )


# rdfs__label: policy
# skos__definition: Encapsulates access logic combining row-level and column-level rules.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/policy
# note: Each policy must have a policy_id and policy_name; may include definition.
class Policy(BaseModel):
    policy_id: str = Field(..., description="Unique identifier for the policy")
    policy_name: str = Field(..., description="Name of the policy")
    definition: Optional[str] = Field(None, description="Optional textual definition")

    # Relationship: (:Policy)-[:hasRowRule]->(:Column)
    # rdfs__label: has row rule
    # skos__definition: Policy includes row-level access condition that applies to a specific column.
    hasRowRule: List[Column] = Field(
        default_factory=list,
        description="Columns referenced by row-level rules (0..N)."
    )

    # Relationship: (:Policy)-[:hasColumnRule]->(:Column)
    # rdfs__label: has column rule
    # skos__definition: Policy includes column-level masking logic that applies to a specific column.
    hasColumnRule: List[Column] = Field(
        default_factory=list,
        description="Columns referenced by column-level masking rules (0..N)."
    )


# rdfs__label: policy group
# skos__definition: A collection of policies aligned to a persona function or role set.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/policy_group
# note: Each policy group must have a policy_group_id and policy_group_name; may include definition.
class PolicyGroup(BaseModel):
    policy_group_id: str = Field(..., description="Unique identifier for the policy group")
    policy_group_name: str = Field(..., description="Name of the policy group")

    # Relationship: (:PolicyGroup)-[:includesPolicy]->(:Policy)
    # rdfs__label: includes policy
    # skos__definition: Policy group bundles policies.
    includesPolicy: List[Policy] = Field(
        default_factory=list,
        description="Policies included in this group (0..N)."
    )


# rdfs__label: user
# skos__definition: Subject or principal entitled to policy groups.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/user
# note: Example user Alice with membership to a policy group.
class User(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    username: Optional[str] = Field(None, description="Display name")

    # Relationship: (:User)-[:memberOf]->(:PolicyGroup)
    # rdfs__label: member of
    # skos__definition: User inherits policies through group membership.
    memberOf: List[PolicyGroup] = Field(
        default_factory=list,
        description="Policy groups the user belongs to (0..N)."
    )