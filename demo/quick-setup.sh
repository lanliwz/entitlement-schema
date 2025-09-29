# 1) Install packages
bash demo/scripts/setup_env.sh
# 2) Seed data, make sure you install mysql and neo4j and start them
mysql.server start
mysql -h 127.0.0.1 -P 3306 -u root -p < demo/scripts/seed_mysql.sql
python -m demo.neo4j_data_loader
# 3) Run demo
python -m demo.run_demo