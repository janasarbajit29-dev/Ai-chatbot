import psycopg2
from app.core.config import settings

try:
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("SELECT current_database();")
    dbname = cursor.fetchone()[0]
    print(f"Connected to Database: {dbname}")
    
    try:
        cursor.execute("SELECT id, name, email FROM users;")
        users = cursor.fetchall()
        print(f"Users in {dbname}:", users)
    except Exception as e:
        print("Could not query users:", e)
            
except Exception as e:
    print("Error:", e)
