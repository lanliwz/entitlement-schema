from graph_database.entitlement_util import *

repo = EntitlementRepository()
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