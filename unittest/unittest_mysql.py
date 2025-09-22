from relational_database.mysql.mysql_connection import *

conn = mysql_connection()
print(mysql_query("select * from bank.employee",conn))