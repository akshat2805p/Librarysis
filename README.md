# Library Management System

A web-based application to manage library operations, including book tracking, borrowing/returning workflows, and fine calculation. Built with Python (Flask) and MySQL.

## Screenshots

### Modern Login Interface
Featuring a glassmorphism design with secure authentication (including Google Login).
![Login Page](images%20desktop/loginpage.png)

### User Dashboard
Personalized dashboard showing active borrows, due dates, and real-time stats.
![Dashboard](images%20desktop/Dashboard.png)

### Book Catalog
Browse the complete collection with search, pagination, and instant availability status.
![Catalog](images%20desktop/Catalog.png)

---

## Features

*   **Authentication**: Secure user login/registration and Social Login (Google).
*   **Role-Based Access**: Separate interfaces for **Admins** (Inventory management) and **Members** (Borrowing history).
*   **Inventory Management**: Add, update, and track book copies.
*   **Circulation**: Issue and return books with automated due date calculation (14 days).
*   **Fine System**: Automatic calculation of late fees (₹10/day).
*   **Search**: Filter books by title or author.

## Tech Stack

*   **Backend**: Python, Flask
*   **Database**: MySQL
*   **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
*   **Styling**: Custom CSS with Glassmorphism aesthetic

## Setup Instructions

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd Library
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Database Configuration**:
    *   Create a MySQL database named `library_db`.
    *   Import the schema from `database/schema.sql`.
    *   Update `app/__init__.py` or `.env` with your DB credentials.

4.  **Run the Application**:
    ```bash
    python run.py
    ```
    Access the app at `http://127.0.0.1:8000`.

## License

This project is for educational purposes.
