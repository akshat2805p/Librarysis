from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import mysql
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors
import datetime

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        role = 'admin' if '@admin.com' in email else 'member'
        
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)", (username, email, hashed_password, role))
            mysql.connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        finally:
            cursor.close()
            
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.index'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Fetch User Details
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (session['user_id'],))
    user_info = cursor.fetchone()
    
    if session['role'] == 'admin':
        cursor.execute("""
            SELECT t.transaction_id, u.username, b.title, b.image_url, t.borrow_date, t.due_date, t.return_date, t.fine_amount, t.status 
            FROM transactions t
            JOIN users u ON t.user_id = u.user_id
            JOIN books b ON t.book_id = b.book_id
            ORDER BY t.borrow_date DESC
        """)
        transactions = cursor.fetchall()
        
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        
        cursor.close()
        return render_template('dashboard.html', transactions=transactions, books=books, is_admin=True, user_info=user_info)
    else:
        # User: My Current Borrows (With Images)
        cursor.execute("""
            SELECT t.transaction_id, b.title, b.image_url, t.borrow_date, t.due_date, t.fine_amount, t.status 
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            WHERE t.user_id = %s AND t.status = 'issued'
        """, (session['user_id'],))
        my_books = cursor.fetchall()
        
        cursor.execute("SELECT * FROM books WHERE available_copies > 0")
        available_books = cursor.fetchall()
        
        cursor.close()
        return render_template('dashboard.html', my_books=my_books, available_books=available_books, is_admin=False, user_info=user_info)


@bp.route('/add_book', methods=['POST'])
def add_book():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('main.index'))
    
    title = request.form['title']
    isbn = request.form['isbn']
    copies = request.form['copies']
    year = request.form['year']
    
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("INSERT INTO books (title, isbn, total_copies, available_copies, publication_year) VALUES (%s, %s, %s, %s, %s)", 
                       (title, isbn, copies, copies, year))
        mysql.connection.commit()
        flash('Book added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding book: {str(e)}', 'danger')
    finally:
        cursor.close()
        
    return redirect(url_for('main.dashboard'))

@bp.route('/books')
def catalog():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    limit = 12
    offset = (page - 1) * limit
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = """
        SELECT b.*, a.name as author_name 
        FROM books b 
        LEFT JOIN authors a ON b.author_id = a.author_id
    """
    params = []
    
    if search_query:
        query += " WHERE b.title LIKE %s OR a.name LIKE %s"
        search_term = f"%{search_query}%"
        params.extend([search_term, search_term])
        
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cursor.execute(query, tuple(params))
    books = cursor.fetchall()
    
    # Simple count check
    cursor.execute("SELECT COUNT(*) as count FROM books") 
    has_next = len(books) == limit
    
    cursor.close()
    return render_template('catalog.html', books=books, page=page, search_query=search_query, has_next=has_next)

@bp.route('/borrow/confirm/<int:book_id>')
def confirm_borrow(book_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
        
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT b.*, a.name as author_name 
        FROM books b 
        LEFT JOIN authors a ON b.author_id = a.author_id 
        WHERE b.book_id = %s
    """, (book_id,))
    book = cursor.fetchone()
    cursor.close()
    
    if not book:
        return redirect(url_for('main.catalog'))
        
    today = datetime.date.today()
    due_date = today + datetime.timedelta(days=14)
    
    return render_template('borrow_confirm.html', book=book, today=today, due_date=due_date)

@bp.route('/borrow/process/<int:book_id>', methods=['POST'])
def process_borrow(book_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
        
    cursor = mysql.connection.cursor()
    try:
        cursor.callproc('issue_book', (session['user_id'], book_id))
        mysql.connection.commit()
        flash('Book borrowed successfully! Enjoy reading.', 'success')
    except Exception as e:
        flash(f'Error borrowing book: {str(e)}', 'danger')
    finally:
        cursor.close()
        
    return redirect(url_for('main.dashboard'))

@bp.route('/return/<int:transaction_id>')
def return_book_route(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    cursor = mysql.connection.cursor()
    try:
        cursor.callproc('return_book', (transaction_id,))
        mysql.connection.commit()
        flash('Book returned successfully!', 'success')
    except Exception as e:
        flash(f'Error returning book: {str(e)}', 'danger')
    finally:
        cursor.close()
        
    return redirect(url_for('main.dashboard'))

@bp.route('/auth/firebase-login', methods=['POST'])
def firebase_login():
    data = request.get_json()
    email = data.get('email')
    username = data.get('displayName') or email.split('@')[0]
    
    if not email:
        return {'status': 'error', 'message': 'No email provided'}, 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if not user:
        # Register new firebase user
        # We set a placeholder password since they login via Auth provider
        hashed_password = generate_password_hash('firebase_oauth_secret') 
        cursor.execute("INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, 'member')", 
                       (username, email, hashed_password))
        mysql.connection.commit()
        
        # Fetch newly created user
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
    
    cursor.close()
    
    # Login Session
    session['user_id'] = user['user_id']
    session['username'] = user['username']
    session['role'] = user['role']
    
    return {'status': 'success', 'redirect': url_for('main.dashboard')}

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        flash(f'If an account exists for {email}, a password reset link has been sent.', 'info')
        return redirect(url_for('main.login'))
    return render_template('forgot_password.html')
