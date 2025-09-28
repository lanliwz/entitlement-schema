//------------clean up ------------------
MATCH (n) DETACH DELETE n;
// ---------- Constraints (standalone) ----------
CREATE CONSTRAINT unique_userId IF NOT EXISTS
FOR (u:User) REQUIRE u.userId IS UNIQUE;

CREATE CONSTRAINT unique_policyId IF NOT EXISTS
FOR (p:Policy) REQUIRE p.policyId IS UNIQUE;

CREATE CONSTRAINT unique_policyGroupId IF NOT EXISTS
FOR (pg:PolicyGroup) REQUIRE pg.policyGroupId IS UNIQUE;

CREATE CONSTRAINT unique_columnId IF NOT EXISTS
FOR (c:Column) REQUIRE c.columnId IS UNIQUE;

CREATE CONSTRAINT unique_tableId IF NOT EXISTS
FOR (t:Table) REQUIRE t.tableId IS UNIQUE;

CREATE CONSTRAINT unique_schemaId IF NOT EXISTS
FOR (s:Schema) REQUIRE s.schemaId IS UNIQUE;

// ---------- Seed using WITH variables ----------
WITH
  'bank' AS schemaId,
  'bank' AS schemaName,
  [
    {tableId:'employee',   tableName:'employee'},
    {tableId:'department', tableName:'department'}
  ] AS tables,
  [
    {columnId:'bank.employee.salary',        columnName:'salary',    tableId:'employee'},
    {columnId:'bank.department.dept_name',   columnName:'dept_name', tableId:'department'}
  ] AS columns,
  [
    {policyGroupId:'all_employees_pg', policyGroupName:'All Employees'},
    {policyGroupId:'finance_pg',       policyGroupName:'Finance Group'},
    {policyGroupId:'hr_pg',            policyGroupName:'HR Group'},
    {policyGroupId:'it_pg',            policyGroupName:'IT Group'},
    {policyGroupId:'client_support_pg',policyGroupName:'Client Support Team'}
  ] AS groups,
  [
    {policyId:'mask_salary_v1',            policyName:'Mask Salary',
     definition:'Mask salary for bank.employee: masked for all users EXCEPT members of Client Support Team',
     rule:'hasColumnRule', columnId:'bank.employee.salary',      groupId:'all_employees_pg'},

    {policyId:'row_filter_finance_only',   policyName:'Finance Department Only',
     definition:"Allow access only to rows where dept_name = 'Finance'",
     rule:'hasRowRule',  columnId:'bank.department.dept_name',   groupId:'finance_pg'},

    {policyId:'row_filter_hr_only',        policyName:'HR Department Only',
     definition:"Allow access only to rows where dept_name = 'HR'",
     rule:'hasRowRule',  columnId:'bank.department.dept_name',   groupId:'hr_pg'},

    {policyId:'row_filter_it_only',        policyName:'IT Department Only',
     definition:"Allow access only to rows where dept_name = 'IT'",
     rule:'hasRowRule',  columnId:'bank.department.dept_name',   groupId:'it_pg'}
  ] AS policies,
  [
    'user-alice',
    'user-bob',
    'user-carol'
  ] AS users,
  [
    {userId:'user-alice', groupId:'all_employees_pg'},
    {userId:'user-alice', groupId:'finance_pg'},

    {userId:'user-bob',   groupId:'all_employees_pg'},
    {userId:'user-bob',   groupId:'client_support_pg'},

    {userId:'user-carol', groupId:'all_employees_pg'},
    {userId:'user-carol', groupId:'it_pg'}
  ] AS memberships

// Schema
MERGE (s:Schema {schemaId:schemaId})
  ON CREATE SET s.schemaName = schemaName

// Tables
WITH s, tables, columns, groups, policies, users, memberships
UNWIND tables AS t
  MERGE (tbl:Table {tableId:t.tableId})
    ON CREATE SET tbl.tableName = t.tableName
  MERGE (tbl)-[:belongsToSchema]->(s)

// Columns
WITH columns, groups, policies, users, memberships
UNWIND columns AS col
  MATCH (tbl:Table {tableId: col.tableId})
  MERGE (c:Column {columnId: col.columnId})
    ON CREATE SET c.columnName = col.columnName
  MERGE (c)-[:belongsToTable]->(tbl)

// Policy Groups
WITH groups, policies, users, memberships
UNWIND groups AS g
  MERGE (pg:PolicyGroup {policyGroupId: g.policyGroupId})
    ON CREATE SET pg.policyGroupName = g.policyGroupName

// Policies + conditional rule rels + includesPolicy
WITH policies, users, memberships
UNWIND policies AS pol
  MERGE (p:Policy {policyId: pol.policyId})
    ON CREATE SET p.policyName = pol.policyName,
                  p.definition = pol.definition
  WITH pol, p, users, memberships
  MATCH (c:Column {columnId: pol.columnId})
  // CONDITIONAL relationships via FOREACH + CASE (no subqueries)
  FOREACH (_ IN CASE WHEN pol.rule = 'hasColumnRule' THEN [1] ELSE [] END |
    MERGE (p)-[:hasColumnRule]->(c)
  )
  FOREACH (_ IN CASE WHEN pol.rule = 'hasRowRule' THEN [1] ELSE [] END |
    MERGE (p)-[:hasRowRule]->(c)
  )
  WITH pol, p, users, memberships
  MATCH (pg:PolicyGroup {policyGroupId: pol.groupId})
  MERGE (pg)-[:includesPolicy]->(p)

// Users
WITH users, memberships
UNWIND users AS uid
  MERGE (:User {userId: uid})

// Memberships
WITH memberships
UNWIND memberships AS m
  MATCH (u:User {userId: m.userId})
  MATCH (pg:PolicyGroup {policyGroupId: m.groupId})
  MERGE (u)-[:memberOf]->(pg);