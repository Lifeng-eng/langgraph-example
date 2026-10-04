import psycopg

DB_URL = "postgresql://langgraph_user:123456@localhost:5432/langgraph_db?sslmode=disable"

conn = psycopg.connect(DB_URL)
cur = conn.cursor()

# 查看 PostgreSQL 版本信息
cur.execute("SELECT version();")
result = cur.fetchone()
print(f"PostgreSQL 版本：{result[0]}")

cur.close()
conn.close()
