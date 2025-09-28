# 1) Setup
bash scripts/setup_env.sh
# edit .env for creds

# 2) Seed data
 mysql -h 127.0.0.1 -P 3306 -u root -p < scripts/seed_mysql.sql
cypher-shell -u neo4j -p neo4j0001 -f seed_neo4j.cypher

# 3) Run demo
python run_demo.py