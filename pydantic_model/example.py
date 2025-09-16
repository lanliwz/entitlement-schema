from pydantic_model.pydantic_entilement_model import *
# Example data instantiation

sales_schema = Schema(
    schema_id="sch1",
    schema_name="sales"
)

customer_table = Table(
    table_id="tbl1",
    table_name="customer",
    belongsToSchema=sales_schema
)

customer_email_col = Column(
    column_id="col1",
    column_name="customer_email",
    belongsToTable=customer_table
)

mask_email_policy = Policy(
    policy_id="pol1",
    policy_name="mask_email",
    definition="Mask the customer email for non-admin users",
    hasRowRule=[customer_email_col],
    hasColumnRule=[customer_email_col]
)

analysts_group = PolicyGroup(
    policy_group_id="pg1",
    policy_group_name="analysts",
    includesPolicy=[mask_email_policy]
)

alice_user = User(
    user_id="u1",
    username="alice",
    memberOf=[analysts_group]
)

# ---------- Example usage ----------
print(alice_user.model_dump())