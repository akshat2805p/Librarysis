import requests
import MySQLdb
import os
from dotenv import load_dotenv
import random

load_dotenv()

# Subjects to fetch to get a good variety
SUBJECTS = ['fiction', 'science', 'history', 'art', 'business', 'biography', 'romance', 'mystery']
TOTAL_TARGET = 500

def get_books_from_open_library(subject, limit=100):
    url = f"https://openlibrary.org/subjects/{subject}.json?limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('works', [])
    return []

def seed_database():
    try:
        db = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            passwd=os.getenv('MYSQL_PASSWORD'),
            db=os.getenv('MYSQL_DB', 'library_db'),
            autocommit=True
        )
        cursor = db.cursor()
        
        count = 0
        for subject in SUBJECTS:
            if count >= TOTAL_TARGET:
                break
                
            print(f"Fetching {subject} books...")
            works = get_books_from_open_library(subject, limit=80)
            
            for work in works:
                title = work.get('title')
                # Try to get cover
                cover_id = work.get('cover_id')
                image_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else "https://via.placeholder.com/300x450?text=No+Cover"
                
                # Try to get author (first one)
                authors = work.get('authors', [])
                author_name = authors[0]['name'] if authors else "Unknown Author"
                
                # Random year/isbn/copies for demo
                year = random.randint(1900, 2023)
                isbn = str(random.randint(1000000000000, 9999999999999))
                copies = random.randint(1, 10)
                
                # Check Author (Reuse or Insert)
                cursor.execute("SELECT author_id FROM authors WHERE name = %s", (author_name,))
                author_row = cursor.fetchone()
                if author_row:
                    author_id = author_row[0]
                else:
                    cursor.execute("INSERT INTO authors (name) VALUES (%s)", (author_name,))
                    author_id = cursor.lastrowid
                
                # Insert Book
                try:
                    cursor.execute("""
                        INSERT INTO books (title, isbn, author_id, total_copies, available_copies, publication_year, image_url, description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (title, isbn, author_id, copies, copies, year, image_url, f"A book about {subject}."))
                    count += 1
                    print(f"Inserted: {title} ({count})")
                except Exception as e:
                    # Duplicate ISBN etc
                    pass
                    
        print(f"FINISHED! Seeded {count} books.")
        cursor.close()
        db.close()
        
    except Exception as e:
        print(f"Error seeding: {e}")

if __name__ == "__main__":
    seed_database()
