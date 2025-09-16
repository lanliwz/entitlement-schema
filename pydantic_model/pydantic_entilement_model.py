from pydantic import BaseModel, Field
from typing import Optional, Dict


# ------------------- Core Classes -------------------

# rdfs__label: policy
# skos__definition: Encapsulates access logic combining row-level and column-level rules.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/policy
# note: Each policy must have a policy_id and policy_name; may include definition.
class Policy(BaseModel):
    policy_id: str = Field(..., description="Unique identifier for the policy")
    policy_name: str = Field(..., description="Name of the policy")
    definition: Optional[str] = Field(None, description="Optional textual definition for a policy")

    # :Policy -[:hasRowRule]-> :Column
    # rdfs__label: has row rule
    # skos__definition: Policy includes row-level access condition that applies to a specific column.
    def row_rule(self, column_id: str, expression: Optional[str] = None) -> Dict:
        return {
            "from_policy": self.policy_id,
            "to_column": column_id,
            "type": "hasRowRule",
            "expression": expression,
        }

    # :Policy -[:hasColumnRule]-> :Column
    # rdfs__label: has column rule
    # skos__definition: Policy includes column-level masking logic that applies to a specific column.
    def column_rule(self, column_id: str, mask_expression: Optional[str] = None) -> Dict:
        return {
            "from_policy": self.policy_id,
            "to_column": column_id,
            "type": "hasColumnRule",
            "mask_expression": mask_expression,
        }


# rdfs__label: table
# skos__definition: Database table grouping columns within a schema.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/table
# note: Contains columns such as customer_email.
class Table(BaseModel):
    table_id: str = Field(..., description="Unique identifier for the table")
    table_name: str = Field(..., description="Name of the table")

    # :Table -[:belongsToSchema]-> :Schema
    # rdfs__label: belongs to schema
    # skos__definition: A table is always contained in exactly one schema.
    def belongs_to_schema(self, schema_id: str) -> Dict:
        return {
            "from_table": self.table_id,
            "to_schema": schema_id,
            "type": "belongsToSchema",
        }


# rdfs__label: schema
# skos__definition: Database schema grouping tables within a database catalog.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/schema
# note: Schema for tables.
class Schema(BaseModel):
    schema_id: str = Field(..., description="Unique identifier for the schema")
    schema_name: str = Field(..., description="Name of the schema")


# rdfs__label: user
# skos__definition: Subject or principal entitled to policy groups.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/user
# note: Example user Alice with membership to a policy group.
class User(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    username: Optional[str] = Field(None, description="Human-readable name of the user")

    # :User -[:memberOf]-> :PolicyGroup
    # rdfs__label: member of
    # skos__definition: User inherits policies through group membership.
    def member_of(self, policy_group_id: str) -> Dict:
        return {
            "from_user": self.user_id,
            "to_policy_group": policy_group_id,
            "type": "memberOf",
        }


# rdfs__label: policy group
# skos__definition: A collection of policies aligned to a persona function or role set.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/policy_group
# note: Each policy group must have a policy_group_id and policy_group_name; may include definition.
class PolicyGroup(BaseModel):
    policy_group_id: str = Field(..., description="Unique identifier for the policy group")
    policy_group_name: str = Field(..., description="Name of the policy group")

    # :PolicyGroup -[:includesPolicy]-> :Policy
    # rdfs__label: includes policy
    # skos__definition: Policy group bundles policies.
    def includes_policy(self, policy_id: str) -> Dict:
        return {
            "from_policy_group": self.policy_group_id,
            "to_policy": policy_id,
            "type": "includesPolicy",
        }


# rdfs__label: column
# skos__definition: Represents a physical database column.
# uri: http://upupedu.com/ontology/entitlement/tabular_data/column
class Column(BaseModel):
    column_id: str = Field(..., description="Unique identifier for the column")
    column_name: str = Field(..., description="Name of the column")

    # :Column -[:belongsToTable]-> :Table
    # rdfs__label: belongs to table
    # skos__definition: A column is always contained in exactly one table.
    def belongs_to_table(self, table_id: str) -> Dict:
        return {
            "from_column": self.column_id,
            "to_table": table_id,
            "type": "belongsToTable",
        }