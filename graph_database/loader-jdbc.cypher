CALL apoc.load.jdbc(
  'jdbc:oracle:thin:@//HOST:1521/SERVICE',
  'SELECT policy_id, policy_name, policy_type, definition FROM policy'
) YIELD row
WITH collect(row) AS rows
UNWIND rows AS r
MERGE (p:Policy {policyId: toInteger(r.POLICY_ID)})
  ON CREATE SET p.policyName = r.POLICY_NAME,
                p.policyType = coalesce(r.POLICY_TYPE,'HYBRID'),
                p.definition = r.DEFINITION;
