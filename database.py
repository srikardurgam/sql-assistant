import sqlite3
import os
import urllib.request

DB_PATH = "northwind.db"
DB_URL = "https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/refs/heads/main/dist/northwind.db"

def get_db():
    if not os.path.exists(DB_PATH):
        print("Downloading Northwind database...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(DB_URL, headers=headers)
        with urllib.request.urlopen(req) as response, open(DB_PATH, 'wb') as out_file:
            out_file.write(response.read())
        print("Download complete.")
    return sqlite3.connect(DB_PATH)

def get_schema():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]

    schema_parts = []
    for table in tables:
        cursor.execute(f'PRAGMA table_info("{table}");')
        columns = cursor.fetchall()
        col_defs = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
        schema_parts.append(f'Table: "{table}"\nColumns: {col_defs}')

    conn.close()
    return "\n\n".join(schema_parts), tables

def run_query(sql):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(sql)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchmany(100)
    conn.close()
    return columns, rows
