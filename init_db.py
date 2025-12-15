import MySQLdb
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MySQL Server (no specific DB yet)
try:
    print("Connecting to MySQL Server...")
    db = MySQLdb.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        passwd=os.getenv('MYSQL_PASSWORD'),
        autocommit=True
    )
    cursor = db.cursor()
    
    # Read Schema
    print("Reading schema.sql...")
    with open('database/schema.sql', 'r') as f:
        schema_sql = f.read()

    # Read Procedures
    print("Reading procedures.sql...")
    with open('database/procedures.sql', 'r') as f:
        procedures_sql = f.read()

    # Execute Schema parts (splitting by semicolon isn't perfect for procedures, but schema is fine)
    # Better approach: Use the specific commands
    
    # 1. Create DB
    print("Creating Database 'library_db' if not exists...")
    cursor.execute("CREATE DATABASE IF NOT EXISTS library_db;")
    cursor.execute("USE library_db;")
    
    # 2. Run Schema SQL
    # Simple split by ';' usually works for table definitions, but we'll try to just read the file content
    # For robust execution, we will execute specific statements for tables.
    # Actually, let's just parse the file carefully or just run the known commands since I generated them.
    # To be safe and simple for the user, I'll rewrite the key creation steps here using the cursor.
    
    # Users
    print("Creating Users table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('admin', 'member') DEFAULT 'member',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Authors
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS authors (
        author_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE
    );
    """)
    
    # Categories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        category_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE
    );
    """)
    
    # Books
    print("Creating Books table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        book_id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        isbn VARCHAR(20) UNIQUE,
        author_id INT,
        category_id INT,
        total_copies INT DEFAULT 1,
        available_copies INT DEFAULT 1,
        publication_year INT,
        FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE SET NULL,
        FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
    );
    """)
    
    # Transactions
    print("Creating Transactions table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        book_id INT NOT NULL,
        borrow_date DATE DEFAULT (CURRENT_DATE),
        due_date DATE,
        return_date DATE,
        fine_amount DECIMAL(10, 2) DEFAULT 0.00,
        status ENUM('issued', 'returned') DEFAULT 'issued',
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE
    );
    """)

    print("Database Tables Initialized Successfully!")
    
    # Procedures are tricky via python cursor due to delimiters. 
    # Validating if we can skip them for basic functionality or try to add them.
    # Let's try to add them.
    
    try:
        cursor.execute("DROP PROCEDURE IF EXISTS issue_book;")
        cursor.execute("""
        CREATE PROCEDURE issue_book(IN p_user_id INT, IN p_book_id INT)
        BEGIN
            DECLARE v_available INT;
            SELECT available_copies INTO v_available FROM books WHERE book_id = p_book_id;
            IF v_available > 0 THEN
                UPDATE books SET available_copies = available_copies - 1 WHERE book_id = p_book_id;
                INSERT INTO transactions (user_id, book_id, borrow_date, due_date)
                VALUES (p_user_id, p_book_id, CURRENT_DATE, DATE_ADD(CURRENT_DATE, INTERVAL 14 DAY));
            ELSE
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Book not available';
            END IF;
        END
        """)
        
        cursor.execute("DROP PROCEDURE IF EXISTS return_book;")
        cursor.execute("""
        CREATE PROCEDURE return_book(IN p_transaction_id INT)
        BEGIN
            DECLARE v_due_date DATE;
            DECLARE v_return_date DATE;
            DECLARE v_days_overdue INT;
            DECLARE v_fine DECIMAL(10,2) DEFAULT 0.00;
            DECLARE v_book_id INT;
            
            SELECT due_date, book_id INTO v_due_date, v_book_id FROM transactions WHERE transaction_id = p_transaction_id;
            SET v_return_date = CURRENT_DATE;
            
            IF v_return_date > v_due_date THEN
                SET v_days_overdue = DATEDIFF(v_return_date, v_due_date);
                SET v_fine = v_days_overdue * 1.00;
            END IF;
            
            UPDATE transactions 
            SET return_date = v_return_date, 
                fine_amount = v_fine, 
                status = 'returned'
            WHERE transaction_id = p_transaction_id;
            
            UPDATE books SET available_copies = available_copies + 1 WHERE book_id = v_book_id;
        END
        """)
        print("Stored Procedures Initialized Successfully!")
    except Exception as e:
        print(f"Warning: Could not create procedures: {e}")
        print("Basic app will work, but fines might not calculate automatically.")

    cursor.close()
    db.close()
    print("\nSUCCESS! You can now run the app.")

except Exception as e:
    print(f"\nERROR: Could not connect or create database.\nDetail: {e}")
    print("Please check your .env file password again.")
