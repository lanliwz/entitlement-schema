# Entitlement 

## Relational Database Schema Design

Entitlement schema is designed to enhance security and control access to a SQL database at both the column and row levels. This schema utilizes policy groups linked to a policy table, where each policy delineates access permissions with precision. Specifically, a policy can define which database schema, table, and column a user or group of users can access. Furthermore, it specifies the values within that column that are permissible for viewing. Additionally, the schema includes functionality to mask certain columns, restricting the visibility of sensitive data. This system allows for a granular level of access control, ensuring that users only have access to the data necessary for their roles, thereby enhancing data security and compliance with data protection regulations.

![policy-group-relationship.png](resource%2Fpolicy-group-relationship.png)

## Graph Schema Design
