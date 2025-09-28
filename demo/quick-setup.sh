# 1) Setup
bash scripts/setup_env.sh
# edit .env for creds

# 2) Seed data
mysql -h 127.0.0.1 -P 3306 -u root -p < scripts/seed_mysql.sql
python neo4j_data_loader.py

# 3) Run demo
python run_demo.py