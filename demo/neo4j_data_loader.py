from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

def load_cypher_file(uri, user, password, filepath):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        with open(filepath, "r", encoding="utf-8") as f:
            cypher_script = f.read()

        # Remove comment lines (// ...)
        cleaned_lines = []
        for line in cypher_script.splitlines():
            striped = line.strip()
            if not striped or striped.startswith("//"):  # skip empty + comment
                continue
            cleaned_lines.append(line)
        cleaned_script = "\n".join(cleaned_lines)

        # Split into individual statements by semicolon
        statements = [s.strip() for s in cleaned_script.split(";") if s.strip()]

        for stmt in statements:
            print(f"Executing: {stmt[:80]}...")
            session.run(stmt)
    driver.close()
    print("✔ Loaded seed cypher into Neo4j (comments ignored)")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cypher_file = os.path.join(base_dir, "scripts", "seed_neo4j.cypher")
    print(os.getenv("Neo4j_Url"))
    print(os.getenv("Neo4j_UserName"))
    print(os.getenv("Neo4j_Password"))
    load_cypher_file(
        uri=os.getenv("Neo4j_Url"),
        user=os.getenv("Neo4j_UserName"),
        password=os.getenv("Neo4j_Password"),
        filepath=cypher_file
    )