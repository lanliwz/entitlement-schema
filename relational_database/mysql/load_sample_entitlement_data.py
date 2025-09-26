from graph_database.entitlement_util import *

repo = EntitlementRepository()

mask_policy_1 = repo.add_mask_policy(
    schema_id="bank",
    schema_name="bank",
    table_id="bank.employee",
    table_name="employee",
    column_id="bank.employee.salary",
    column_name="salary",
    policy_id="mask_salary",
    policy_name="Mask salary",
    definition="Full mask salary as numeric value of 0.00",
    policy_group_id="enterprise_masking_policy_group",
    policy_group_name="Default Masking Policy Group"
)

mask_policy_2 = repo.add_mask_policy(
    schema_id="bank",
    schema_name="bank",
    table_id="bank.employee",
    table_name="employee",
    column_id="bank.employee.salary",
    column_name="salary",
    policy_id="no_mask_salary",
    policy_name="No Mask salary",
    definition="No mask for salary, salary value should be viewed as it is",
    policy_group_id="highly_privileged_support_group",
    policy_group_name="Highly Privileged Support Group"
)


for dept, pg_id, pg_name in [
    ("HR", "bank_hr_pg", "HR Group"),
    ("IT", "bank_it_pg", "IT Group"),
    ("Finance", "bank_finance_pg", "Finance Group"),
]:
    pid = f"row_filter_{dept.lower()}"
    pname = f"{dept} Department"
    definition = f"Allow access to rows where dept_name = '{dept}'"

    created = repo.add_row_policy(
        schema_id="bank", schema_name="bank",
        table_id="department", table_name="department",
        column_id="bank.department.dept_name", column_name="dept_name",
        policy_id=pid, policy_name=pname, definition=definition,
        policy_group_id=pg_id, policy_group_name=pg_name
    )
    print(f"{dept} row policy:", created)

for pg_id, pg_name in [
    ("bank_hr_pg", "HR Group"),
    ("bank_it_pg", "IT Group"),
    ("bank_finance_pg", "Finance Group"),
    ("highly_privileged_support_group", "Highly Privileged Support Group"),

]:
    client_support_group = repo.add_user_to_policy_group(
        user_id="user-alice",   # example user
        policy_group_id=pg_id,
        policy_group_name=pg_name
    )



for pg_id, pg_name in [
    ("bank_it_pg", "IT Group"),
    ("enterprise_masking_policy_group", "Default Masking Policy Group")
]:
    client_support_group = repo.add_user_to_policy_group(
        user_id="user-bob",   # example user
        policy_group_id=pg_id,
        policy_group_name=pg_name
    )

print("\nuser-alice \n")
entitlements = repo.fetch_entitlements(
    user_id="user-alice",
    schema_name="bank",
    table_name="employee"
)

for e in entitlements:
    print(e)

entitlements = repo.fetch_entitlements(
    user_id="user-alice",
    schema_name="bank",
    table_name="department"
)

for e in entitlements:
    print(e)

print("\nuser-bob \n")
entitlements = repo.fetch_entitlements(
    user_id="user-bob",
    schema_name="bank",
    table_name="employee"
)


for e in entitlements:
    print(e)

entitlements = repo.fetch_entitlements(
    user_id="user-bob",
    schema_name="bank",
    table_name="department"
)

for e in entitlements:
    print(e)
repo.close()