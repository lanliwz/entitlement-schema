# Entitlement 

## Relational Database Schema Design

The entitlement schema is designed to provide granular, policy-driven access control for SQL databases, securing data at both the row level and column level.

At the core of the model are policies, which represent access rules. Policies can incorporate:
*   Row filter rules that define which rows a subject may see, based on schema, table, column, and value filters.
*   Column mask rules that specify how sensitive column values should be transformed or hidden before being presented.

Policies are bundled into policy groups, which represent higher-level personas or role sets. Users (or other subjects) are assigned to policy groups via entitlements, ensuring that each subject inherits the correct set of policies.

The schema also explicitly models the database schema, table, and column metadata, ensuring that every rule is traceable to the physical data structure it governs. Each relationship between a policy, rule, column, and table is captured, along with descriptive annotations, status flags, and effective dates, supporting both operational enforcement and governance review.

This design provides:
* 	Row-level security by filtering permissible data values per user or group.
* 	Column-level security by masking or redacting sensitive fields.
* 	Policy grouping for simplified administration and persona-based entitlements.
* 	Auditability and compliance support through explicit tracking of rules, assignments, and their lifecycle status.

By combining these features, the schema ensures that users can access only the data necessary for their role, thereby strengthening overall data protection and facilitating compliance with regulatory requirements.

![policy-group-relationship.png](resource%2Fpolicy-group-relationship.png)

# Ontology / Neo4j Schema Design

The **entitlement ontology** is designed to represent **fine-grained access control policies** in a graph model, enabling flexible reasoning, visualization, and governance. All entities are modeled as `:owl__Class` nodes with a **lowercase `rdfs__label`** and a **`skos__definition`** describing their semantics.  

---

## Core Concepts

- **policy**: Encapsulates access logic, combining row-level and column-level rules.  
- **policy group**: A collection of policies aligned to a persona, function, or role set.
- **column**: Represent physical database structures, with properties such as `schema_name`, `table_name`, and `column_name` captured as data properties on the corresponding nodes.  
- **user**: Represents a subject or principal entitled to policy groups.

---

## Relationships

- `(:policy)-[:hasRowRule]->(:column)` — Policy includes row-level access conditions. Row rule applies to a specific column.  
- `(:policy)-[:hasColumnRule]->(:column)` — Policy includes column-level masking logic. Mask rule applies to a specific column.
- `(:user)-[:memberOf]->(:policy group)` — User inherits policies through group membership.  
- `(:policy group)-[:includesPolicy]->(:policy)` — Policy groups bundle policies.

Each relationship is annotated with a **`skos__definition`** to capture its semantics (e.g., “column mask rule applies to a specific column”).  

---

## Data Properties

Each `:owl__Class` instance carries **required (R)** and **optional (O)** properties based on the relational schema:  

### policy
- `policy_id` (R)  
- `policy_name` (R)  
- `policy_type` (O)  
- `definition` (O)  

### policy group
- `policy_group_id` (R)  
- `policy_group_name` (R)  
- `group_type` (O)  
- `definition` (O)  

### [:hasRowRule]
- `filter_operator` (R)  
- `match_value` (R)  
- `description` (O)  

### [:hasColumnRule]
- `mask_algorithm` (O)  
- `description` (O)  


### column
- `schema_name` (R)  
- `table_name` (R)  
- `column_name` (R)  
- Optional metadata: `data_type`, `data_length`, `nullable`, etc.  

### user
- `user_id` (R)  


### [:memberOf]
- `status` (R)  
- `granted_at` (R)  
- `revoked_at` (O)  

## Benefits

- **Traceability**: Every rule directly links to the physical column and table it governs.  
- **Granularity**: Policies can be expressed at both row and column level.  
- **Flexibility**: Policy groups allow scalable assignment of multiple policies to multiple users.  
- **Semantics & reasoning**: `skos__definition` and `rdfs__label` ensure clear meaning, enabling reasoning engines and governance tooling to interpret access models.  
- **Audit & compliance**: Graph relationships and lifecycle properties (`status`, timestamps) make it possible to query, certify, and audit entitlements end-to-end.  

---
