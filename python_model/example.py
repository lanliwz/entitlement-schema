from python_model.entitlement_pydantic_class import *
# Example data instantiation

# OpenAI Prompt
# create example for exployee table, which has department column, \n
# which has row level policy associated with department name, \n
# and ssn, which has masking policy for last 4 digit \n

# ---------- Core nodes ----------
hr_schema = Schema(
    schema_id="sch_hr",
    schema_name="hr"
)

employee_table = Table(
    table_id="tbl_employee",
    table_name="employee",
    belongsToSchema=hr_schema
)

department_col = Column(
    column_id="col_department",
    column_name="department",
    belongsToTable=employee_table
)

ssn_col = Column(
    column_id="col_ssn",
    column_name="ssn",
    belongsToTable=employee_table
)

# ---------- Policies ----------
# Row-level policy: only rows where department='Engineering'
dept_row_policy = Policy(
    policy_id="pol_dept_eng_only",
    policy_name="department_engineering_only",
    definition="Allow only rows where department = 'Engineering'",
    hasRowRule=[department_col]      # link to the department column
)

# Column masking policy: mask SSN to show only last 4 digits
ssn_mask_policy = Policy(
    policy_id="pol_mask_ssn_last4",
    policy_name="mask_ssn_last4",
    definition="Mask SSN for non-privileged users, exposing only the last 4 digits",
    hasColumnRule=[ssn_col]          # link to the ssn column
)

# Optional: a policy group bundling both policies
hr_analysts_group = PolicyGroup(
    policy_group_id="pg_hr_analysts",
    policy_group_name="HR Analysts",
    includesPolicy=[dept_row_policy, ssn_mask_policy]
)

# Optional: a user who belongs to the policy group
alice = User(
    user_id="u_alice",
    username="Alice",
    memberOf=[hr_analysts_group]
)
# ---------- Example usage ----------
import pydantic
print(pydantic.version.VERSION)
print(alice.model_dump_json(indent=2))