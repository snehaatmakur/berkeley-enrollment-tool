import sqlite3
import json

conn = sqlite3.connect('catalog.db')
cursor = conn.cursor()

# Query prerequisites for COMPSCI 164 (or any course you want to inspect)
cursor.execute('''
    SELECT course_code, prereq_json 
    FROM prerequisites 
    WHERE course_code LIKE '%189%' OR course_code LIKE '%61B%'
''')

rows = cursor.fetchall()
for code, prereq_raw in rows:
    print(f"=== {code} ===")
    parsed_json = json.loads(prereq_raw)
    print(json.dumps(parsed_json, indent=2))
    print("\n")

conn.close()