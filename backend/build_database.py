import pandas as pd
import requests
import sqlite3
import json
import time

# 1. Database Setup
def setup_database():
    print("Initializing SQLite database...")
    # This creates a local file named 'catalog.db' in your folder
    conn = sqlite3.connect('catalog.db')
    cursor = conn.cursor()
    
    # Create the main classes table from the CSV data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            course_code TEXT PRIMARY KEY,
            course_title TEXT,
            units TEXT,
            description TEXT
        )
    ''')
    
    # Create the separate prerequisites table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prerequisites (
            course_code TEXT PRIMARY KEY,
            prereq_json TEXT,
            FOREIGN KEY(course_code) REFERENCES courses(course_code)
        )
    ''')
    
    conn.commit()
    return conn

# 2. API Helper: Get all the secret IDs
def get_course_id_mapping():
    print("Fetching master ID mapping from Coursedog API...")
    url = "https://app.coursedog.com/api/v1/cm/ucberkeley_peoplesoft/courses/search/%24filters?catalogId=hMSTjIplK6VX5nnJn7ZE&skip=0&limit=150&orderBy=code"
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://undergraduate.catalog.berkeley.edu",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "x-requested-with": "catalog"
    }
    
    payload = {
        "condition": "AND",
        "filters": [
            {
                "filters": [
                    {"id": "status-course", "condition": "field", "name": "status", "inputType": "select", "group": "course", "type": "is", "value": "Active", "customField": False}
                ],
                "id": "QAg3zukO",
                "condition": "and"
            },
            {
                "condition": "AND",
                "filters": [
                    {"group": "course", "id": "subjectCode-course", "inputType": "subjectCodeSelect", "name": "subjectCode", "type": "is", "value": "COMPSCI"}
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    mapping = {}
    if response.status_code == 200:
        data = response.json()
        for item in data.get("data", []):
            code = item.get("code")
            group_id = item.get("courseGroupId")
            if code and group_id:
                mapping[code] = group_id
    return mapping

# 3. API Helper: Get specific prerequisites
def get_prerequisites(group_id):
    url = f"https://app.coursedog.com/api/v1/cm/ucberkeley_peoplesoft/courses/search/$filters?courseGroupIds={group_id}&formatDependents=true"
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": "https://undergraduate.catalog.berkeley.edu",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "x-requested-with": "catalog"
    }
    
    payload = {
        "filters": [{"id": "status-course", "condition": "field", "name": "status", "inputType": "select", "group": "course", "type": "is", "value": "Active", "customField": False}],
        "id": "QAg3zukO",
        "condition": "and"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            return data["data"][0].get("requisites")
    return None

# 4. Main Execution Pipeline
def build_full_database():
    conn = setup_database()
    cursor = conn.cursor()
    
    # Load the CSV using pandas
    print("Reading CSV file...")
    try:
        df = pd.read_csv('compsci_courses.csv')
    except FileNotFoundError:
        print("Error: Could not find 'compsci_courses.csv' in the folder.")
        return

    # Grab the API mapping
    id_map = get_course_id_mapping()
    
    print(f"Processing {len(df)} courses into the database...")
    
    for index, row in df.iterrows():
        # Clean up the course code string (e.g., "COMPSCI 164" -> "COMPSCI164" or whatever matches the CSV)
        # We assume the CSV has columns like 'Subject', 'Course Number', 'Course Title'
        subject = str(row.get('Subject', '')).strip()
        number = str(row.get('Course Number', '')).strip()
        course_code = f"{subject} {number}".strip()
        
        title = str(row.get('Course Title', ''))
        units = str(row.get('Minimum Units', ''))
        description = str(row.get('Course Description', ''))
        
        # Insert into the main courses table
        cursor.execute('''
            INSERT OR REPLACE INTO courses (course_code, course_title, units, description)
            VALUES (?, ?, ?, ?)
        ''', (course_code, title, units, description))
        
        # Look up the ID to fetch prerequisites
        # Sometimes the API removes spaces, so we check both "COMPSCI 164" and "COMPSCI164"
        group_id = id_map.get(course_code) or id_map.get(course_code.replace(" ", ""))
        
        if group_id:
            prereq_data = get_prerequisites(group_id)
            prereq_json_str = json.dumps(prereq_data) if prereq_data else "{}"
            
            # Insert into the prerequisites table
            cursor.execute('''
                INSERT OR REPLACE INTO prerequisites (course_code, prereq_json)
                VALUES (?, ?)
            ''', (course_code, prereq_json_str))
            
            print(f"Saved: {course_code} - Prereqs logic stored.")
            time.sleep(0.5) # Polite scraping delay
        else:
            print(f"Skipped Prereqs for {course_code}: Could not find API ID.")
            
    conn.commit()
    conn.close()
    print("\nDatabase build complete! Data saved to 'catalog.db'.")

if __name__ == "__main__":
    build_full_database()