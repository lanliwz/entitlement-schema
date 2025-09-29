#!/usr/bin/env bash
set -euo pipefail

# Need to have python 3.13 or above
python -V
# 👇 add/adjust versions to match your env
pip install "langgraph>=0.2.33" "langchain>=0.3.0" "langchain-openai>=0.2.2"
pip install neo4j acryl-sqlglot mysql-connector-python jaydebeapi datahub

# download mysql jar
https://dev.mysql.com/downloads/connector
# make sure you have jdk, which is needed for mysql jdbc connection
brew update
brew install openjdk@17
echo 'export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"' >> ~/.zshrc
echo 'export CPPFLAGS="-I/opt/homebrew/opt/openjdk@17/include"' >> ~/.zshrc
source ~/.zshrc



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