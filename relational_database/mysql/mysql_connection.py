import os
from typing import Any, Dict, List
import jaydebeapi
from secret.secret_util import get_config

# Make sure this matches your system (Apple Silicon example shown)
os.environ["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"

def mysql_connection():
    """
    Create a MySQL JDBC connection via jaydebeapi using values from config['mysql'].
    Returns:
        - jaydebeapi connection on success
        - {'error': '<message>'} on failure
    """
    import jaydebeapi
    config = get_config()
    JDBC_JAR = config['mysql']["JDBC_JAR"]
    JDBC_URL = config['mysql']["JDBC_URL"]
    USERNAME = config['mysql']["USERNAME"]
    PASSWORD = config['mysql']["PASSWORD"]
    DRIVER = config['mysql']["DRIVER"]

    try:
        # print(f"{JDBC_URL} {JDBC_JAR} {DRIVER} {USERNAME} {PASSWORD}")
        conn = jaydebeapi.connect(
            jclassname=DRIVER,
            url=JDBC_URL,
            driver_args=[USERNAME, PASSWORD],
            jars=JDBC_JAR
        )
        return conn
    except Exception as e:
        return {"error": str(e)}


def mysql_query(sql: str, conn) -> List[Dict[str, Any]]:
    """
    Run a SELECT (or any result-producing) SQL on the given MySQL connection.
    Returns:
        - List[Dict[str, Any]] of rows
        - [{'error': '<message>'}] on failure
    """
    if isinstance(conn, dict) and "error" in conn:
        return [conn]
    try:
        curs = conn.cursor(dictionary=True)
        curs.execute(sql)
        rows = curs.fetchall()
        curs.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]


# conn = mysql_connection()
# result = mysql_query("select * from employee",conn)
# print(result)