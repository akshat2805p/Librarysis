import MySQLdb
import os
from dotenv import load_dotenv

load_dotenv()

try:
    print("Connecting to database...")
    db = MySQLdb.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        passwd=os.getenv('MYSQL_PASSWORD'),
        db=os.getenv('MYSQL_DB', 'library_db'),
        autocommit=True
    )
    cursor = db.cursor()

    print("Adding 'image_url' column...")
    try:
        cursor.execute("ALTER TABLE books ADD COLUMN image_url VARCHAR(500) DEFAULT 'https://via.placeholder.com/150';")
        print("image_url added.")
    except Exception as e:
        print(f"Skipping image_url (might exist): {e}")

    print("Adding 'description' column...")
    try:
        cursor.execute("ALTER TABLE books ADD COLUMN description TEXT;")
        print("description added.")
    except Exception as e:
        print(f"Skipping description (might exist): {e}")

    cursor.close()
    db.close()
    print("Migration Complete.")

except Exception as e:
    print(f"Error during migration: {e}")
