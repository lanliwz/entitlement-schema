from typing import Any, Dict, List
import jaydebeapi
from secret.secret_util import get_config

# Load all config once
config = get_config()

# ---- MySQL config pulled from [mysql] section ----
JDBC_JAR = config['mysql']["JDBC_JAR"]
JDBC_URL = config['mysql']["JDBC_URL"]
USERNAME = config['mysql']["USERNAME"]
PASSWORD = config['mysql']["PASSWORD"]
DRIVER = config['mysql']["DRIVER"]

def mysql_connection():
    """
    Create a MySQL JDBC connection via jaydebeapi using values from config['mysql'].
    Returns:
        - jaydebeapi connection on success
        - [{'error': '<message>'}] on failure (keeps parity with your oracle_* helpers)
    """

    try:
        conn = jaydebeapi.connect(
            DRIVER,
            JDBC_URL,
            [USERNAME, PASSWORD],
            JDBC_JAR,
        )
        return conn
    except Exception as e:
        return [{"error": str(e)}]


def mysql_query(sql: str, conn) -> List[Dict[str, Any]]:
    """
    Run a SELECT (or any result-producing) SQL on the given MySQL connection.
    Returns:
        - List[Dict[str, Any]] of rows
        - [{'error': '<message>'}] on failure
    """
    try:
        curs = conn.cursor()
        curs.execute(sql)
        cols = [d[0] for d in curs.description] if curs.description else []
        rows = [dict(zip(cols, r)) for r in curs.fetchall()] if cols else []
        curs.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]