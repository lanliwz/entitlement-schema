# Entitlement Schema

## Mission statement

**Protecting sensitive data is no longer optional.**

Data protection is now both an operational requirement and a legal requirement:

- Operationally: teams need row-level and column-level controls to reduce exposure, enforce least-privilege access, and keep policy behavior transparent across distributed datasets.
- Legally: multiple frameworks require safeguards and accountable access controls, including:
  - `GDPR` (EU 2016/679, in force since May 25, 2018), including significant administrative fines under Article 83.
  - `CCPA/CPRA` in California (CPRA amendments effective January 1, 2023), establishing consumer privacy rights and enforcement obligations.
  - `HIPAA Security Rule` (45 CFR Part 160 and Subparts A/C of Part 164), requiring administrative, physical, and technical safeguards for ePHI.
  - `FTC Safeguards Rule` (16 CFR Part 314), requiring covered financial institutions to maintain a comprehensive information security program.

This project targets:

- Consistent row-level and column-level policy enforcement
- Transparency in how access rules are applied
- Stronger granularity, traceability, and governance than traditional role-only models

This project models data entitlements in Neo4j and enforces them for SQL queries in MySQL.
It supports:

- Row-level filtering (for example, only `dept_name = 'Finance'`)
- Column-level masking (for example, mask `salary`)
- Policy grouping (user -> policy group -> policy)

The demo flow is:

1. Parse input SQL and find referenced tables
2. Load the user's entitlements from Neo4j
3. Rewrite SQL using row and mask rules
4. Execute rewritten SQL in MySQL

## Repository structure

- `demo/run_demo.py`: Demo entry point
- `demo/neo4j_data_loader.py`: Loads Neo4j seed graph
- `demo/scripts/seed_mysql.sql`: Seeds MySQL sample tables/data
- `demo/scripts/seed_neo4j.cypher`: Seeds entitlement graph
- `relational_database/mysql/mysql_entitlement_util.py`: Parse, entitlement fetch, rewrite, execute
- `graph_database/entitlement_util.py`: Neo4j entitlement repository
- `system_config.ini`: Local connection settings

## Prerequisites

- Python 3.11+
- MySQL (local)
- Neo4j (local)
- Java (required by JDBC path used by `jaydebeapi`)
- MySQL Connector/J `.jar`

Install Python packages:

```bash
pip install "langgraph>=0.2.33" "langchain>=0.3.0" "langchain-openai>=0.2.2" \
  neo4j acryl-sqlglot mysql-connector-python jaydebeapi datahub
```

Optional:
- Set `OPENAI_API_KEY` to use LLM rewrite. Without a key, the code uses rule-based rewrite.

## Configuration

Edit `system_config.ini` for your machine:

- `[mysql]`:
  - `JDBC_JAR` path must point to your local MySQL Connector/J jar
  - `JDBC_URL`, `USERNAME`, `PASSWORD`, `DRIVER`
- `[neo4j]`:
  - `URL`, `USERNAME`, `PASSWORD`, `DATABASE`

## Quick start

1. Start MySQL and Neo4j locally.
2. Seed MySQL:

```bash
mysql -h 127.0.0.1 -P 3306 -u root -p < demo/scripts/seed_mysql.sql
```

3. Seed Neo4j:

```bash
python -m demo.neo4j_data_loader
```

4. Run demo:

```bash
python -m demo.run_demo
```

The demo runs sample queries as `user-alice`, `user-bob`, and `user-carol` and prints:
- input SQL
- rewritten SQL
- entitlement trace
- query rows

## Neo4j entitlement model

Node labels:
- `User`
- `PolicyGroup`
- `Policy`
- `Schema`
- `Table`
- `Column`

Relationships:
- `(User)-[:memberOf]->(PolicyGroup)`
- `(PolicyGroup)-[:includesPolicy]->(Policy)`
- `(Policy)-[:hasRowRule]->(Column)`
- `(Policy)-[:hasColumnRule]->(Column)`
- `(Column)-[:belongsToTable]->(Table)`
- `(Table)-[:belongsToSchema]->(Schema)`

## Additional docs

- Demo notes: [demo-readme.md](demo-readme.md)
- MySQL setup notes: [relational_database/mysql/readme.md](relational_database/mysql/readme.md)
- Graph examples: `resource/`

## References

- GDPR (Regulation (EU) 2016/679): https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng
- GDPR Article 83 (administrative fines): https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng#d1e3082-1-1
- California Consumer Privacy Act (CCPA/CPRA): https://oag.ca.gov/privacy/ccpa
- HIPAA Security Rule summary (HHS): https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html
- FTC Safeguards Rule (16 CFR Part 314): https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-314
