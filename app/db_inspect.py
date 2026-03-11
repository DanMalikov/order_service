import os
import psycopg
from psycopg.rows import dict_row

# Получаем строку подключения
db_url = os.environ.get("POSTGRES_CONNECTION_STRING")

if not db_url:
    raise RuntimeError("POSTGRES_CONNECTION_STRING not found in environment variables")

conn = psycopg.connect(db_url)
cur = conn.cursor(row_factory=dict_row)

print("\n=== TABLES ===")

cur.execute("""
SELECT table_name
FROM information_schema.tables
WHERE table_schema='public'
ORDER BY table_name
""")

tables = [row["table_name"] for row in cur.fetchall()]

for table in tables:
    print(f"\nTable: {table}")

    cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = %s
    ORDER BY ordinal_position
    """, (table,))

    for column in cur.fetchall():
        print(f"  {column['column_name']} : {column['data_type']}")

cur.close()
conn.close()