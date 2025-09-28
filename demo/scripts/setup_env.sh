#!/usr/bin/env bash
set -euo pipefail

python -V
# 👇 add/adjust versions to match your env
pip install "langgraph>=0.2.33" "langchain>=0.3.0" langchain-openai==0.2.2 \
            neo4j==5.* sqlglot==25.* mysql-connector-python==9.* python-dotenv==1.*

# ---- ENV VARS (edit for your env) ----
cat > .env << 'EOF'
# Neo4j (entitlement graph)
Neo4jFinDBUrl=bolt://localhost:7687
Neo4jFinDBUserName=neo4j
Neo4jFinDBPassword=neo4j0001

# MySQL (business data)
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=ent_manager
MYSQL_PASSWORD=ent001!
MYSQL_DATABASE=bank

# Optional LLM rewriter (or app will use rule-based fallback)
OPENAI_API_KEY=sk-...

# Demo defaults
TEST_USER_ID=user-alice
TEST_SQL=SELECT e.emp_id, e.first_name, e.last_name, e.salary FROM bank.employee e JOIN bank.department d ON e.dept_id = d.dept_id
EOF

echo "✔ Environment prepared. Edit .env to match your credentials."