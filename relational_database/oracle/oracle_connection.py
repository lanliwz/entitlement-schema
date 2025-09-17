from secret.secret_util import get_config
import jaydebeapi
from typing import Any, Dict, List, Literal, Optional

config = get_config()
jdbc_jar = config['oracle']["JDBC_JAR"]
url = config['oracle']["JDBC_URL"]
user = config['oracle']["USERNAME"]
password = config['oracle']["PASSWORD"]

# get all secret and config params from config
config = get_config()

def oracle_connection():
    if not all([jdbc_jar, url, user, password]):
        return [{"error": "Set ORACLE_JDBC_JAR, ORACLE_URL, ORACLE_USER, ORACLE_PASSWORD env vars"}]
    try:
        conn = jaydebeapi.connect(
            "oracle.jdbc.OracleDriver",
            url,
            [user, password],
            jdbc_jar,
        )
        return conn
    except Exception as e:
        return [{"error": str(e)}]

def oracle_query(sql: str, conn) -> List[Dict[str, Any]]:
    try:
        curs = conn.cursor()
        curs.execute(sql)
        cols = [d[0] for d in curs.description]
        rows = [dict(zip(cols, r)) for r in curs.fetchall()]
        curs.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]