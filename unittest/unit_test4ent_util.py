from graph_database.entitlement_util import *

repo = EntitlementRepository(driver)

records = repo.fetch_entitlements("user-alice", "hr", "employee")


print(records)

# added = repo.add_mask_policy(
#     schema_id="sales", schema_name="sales",
#     table_id="customers", table_name="customers",
#     column_id="sales.customers.customer_email", column_name="customer_email",
#     policy_id="mask_customer_email_v1",
#     policy_name="Mask customer_email",
#     definition="Mask email: keep first 3 chars, replace rest with *",
#     policy_group_id="cust_policy_group", policy_group_name="Customer Policies"
# )
#
# membership = repo.add_user_to_policy_group(
#     user_id="user-alice",
#     policy_group_id="cust_policy_group",
#     policy_group_name="Customer Policies"
# )
#
# print("User membership created:", membership)
#
# print("Added/Ensured:", added)

# attached = repo.add_policy_to_group(
#     policy_id="mask_customer_email_v1",
#     policy_group_id="cust_policy_group",
#     policy_group_name="Customer Policies"
# )
# print(attached)
#
# # 2) Create-or-attach (policy will be created if missing)
# attached2 = repo.add_policy_to_group(
#     policy_id="mask_phone_v1",
#     policy_group_id="cust_policy_group",
#     policy_group_name="Customer Policies",
#     policy_name="Mask phone",
#     definition="Mask phone: keep last 4 digits"
# )
# print(attached2)

row_policy = repo.add_row_policy(
    schema_id="sales", schema_name="sales",
    table_id="orders", table_name="orders",
    column_id="sales.orders.order_amount", column_name="order_amount",
    policy_id="row_filter_high_value_orders",
    policy_name="High Value Orders Only",
    definition="Allow access only to orders where amount > 1000",
    policy_group_id="finance_pg",
    policy_group_name="Finance Group"
)

print("Row policy created:", row_policy)
