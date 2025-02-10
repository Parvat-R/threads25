# import psycopg2
# from psycopg2 import sql
# from psycopg2 import pool

# DB_NAME = "your_dbname"
# DB_USER = "your_username"
# DB_PASSWORD = "your_password"
# DB_HOST = "localhost"
# DB_PORT = "5432"

# # Create a connection pool to manage database connections efficiently
# db_pool = psycopg2.pool.SimpleConnectionPool(
#     minconn=5,  # Minimum 5 connections in the pool
#     maxconn=20,  # Maximum 20 connections in the pool
#     dbname=DB_NAME,
#     user=DB_USER,
#     password=DB_PASSWORD,
#     host=DB_HOST,
#     port=DB_PORT
# )

# def get_db_connection():
#     """Get a connection from the pool"""
#     return db_pool.getconn()

# def release_db_connection(conn):
#     """Release the connection back to the pool"""
#     db_pool.putconn(conn)

# def init_db():
#     """Initialize the database with necessary tables and indexes"""
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     # Create students table with indexes for faster searches
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS students (
#         id SERIAL PRIMARY KEY,
#         name VARCHAR(255) NOT NULL,
#         email VARCHAR(255) UNIQUE NOT NULL,
#         phone VARCHAR(20) UNIQUE NOT NULL,
#         rollno VARCHAR(50) UNIQUE NOT NULL,
#         interested_events TEXT[],
#         attended_events TEXT[],
#         paid BOOLEAN DEFAULT FALSE
#     );
#     """)

#     # Add indexes on frequently searched fields
#     cursor.execute("CREATE INDEX IF NOT EXISTS idx_email ON students(email);")
#     cursor.execute("CREATE INDEX IF NOT EXISTS idx_phone ON students(phone);")
#     cursor.execute("CREATE INDEX IF NOT EXISTS idx_rollno ON students(rollno);")

#     # Create admin table
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS admins (
#         id SERIAL PRIMARY KEY,
#         username VARCHAR(255) UNIQUE NOT NULL,
#         password TEXT NOT NULL
#     );
#     """)

#     conn.commit()
#     cursor.close()
#     release_db_connection(conn)

# def student_exists(email, phone, rollno):
#     """Check if a student already exists"""
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute(
#         "SELECT id FROM students WHERE email=%s OR phone=%s OR rollno=%s",
#         (email, phone, rollno)
#     )
#     result = cursor.fetchone()
#     cursor.close()
#     release_db_connection(conn)
#     return result is not None

# def add_students(students):
#     """
#     Adds multiple students efficiently using batch insert.
#     Expects students as a list of tuples (name, email, phone, rollno, interested_events, attended_events, paid).
#     """
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     query = sql.SQL("""
#         INSERT INTO students (name, email, phone, rollno, interested_events, attended_events, paid)
#         VALUES %s ON CONFLICT (email, phone, rollno) DO NOTHING;
#     """)
    
#     psycopg2.extras.execute_values(cursor, query, students, template=None, page_size=500)
    
#     conn.commit()
#     cursor.close()
#     release_db_connection(conn)

# def get_students(search_query=None, filter_paid=None, limit=100, offset=0):
#     """Fetches students with pagination"""
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     base_query = "SELECT * FROM students"
#     params = []
#     conditions = []

#     if search_query:
#         conditions.append("(LOWER(name) LIKE %s OR LOWER(email) LIKE %s OR LOWER(rollno) LIKE %s)")
#         params.extend([f"%{search_query.lower()}%", f"%{search_query.lower()}%", f"%{search_query.lower()}%"])

#     if filter_paid == "paid":
#         conditions.append("paid = TRUE")
#     elif filter_paid == "not-paid":
#         conditions.append("paid = FALSE")

#     if conditions:
#         base_query += " WHERE " + " AND ".join(conditions)

#     base_query += " ORDER BY id LIMIT %s OFFSET %s"
#     params.extend([limit, offset])

#     cursor.execute(base_query, tuple(params))
#     students = cursor.fetchall()
    
#     cursor.close()
#     release_db_connection(conn)
#     return students

# def update_student(student_id, name, email, phone, rollno, interested_events, attended_events, paid):
#     """Efficiently updates student details"""
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     cursor.execute("""
#         UPDATE students
#         SET name=%s, email=%s, phone=%s, rollno=%s, interested_events=%s, attended_events=%s, paid=%s
#         WHERE id=%s;
#     """, (name, email, phone, rollno, interested_events, attended_events, paid, student_id))
    
#     conn.commit()
#     cursor.close()
#     release_db_connection(conn)

# def delete_student(student_id):
#     """Deletes a student from the database"""
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     cursor.execute("DELETE FROM students WHERE id = %s;", (student_id,))
    
#     conn.commit()
#     cursor.close()
#     release_db_connection(conn)

# def check_admin_password(username, password):
#     """Checks if the admin username and password match"""
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     cursor.execute("SELECT 1 FROM admins WHERE username = %s AND password = %s", (username, password))
#     result = cursor.fetchone()
    
#     cursor.close()
#     release_db_connection(conn)
#     return result is not None

# # Ensure DB is initialized on first run
# if __name__ == "__main__":
#     init_db()



#### BELOW IS THE SQLITE ALTERNATE VERSION
import sqlite3
import json

DB_NAME = "database.sqlite3"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        rollno TEXT UNIQUE NOT NULL,
        interested_events TEXT DEFAULT '[]',
        attended_events TEXT DEFAULT '[]',
        paid BOOLEAN DEFAULT FALSE
    );
    ''')
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_email ON students(email);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_rollno ON students(rollno);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_name ON students(name);")

    conn.commit()
    cur.close()
    conn.close()

def student_exists(email, phone, rollno):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM students WHERE email = ? OR phone = ? OR rollno = ?", (email, phone, rollno))
    exists = cur.fetchone()
    cur.close()
    conn.close()
    return exists is not None

def add_student(name, email, phone, rollno, interested_events, attended_events=[], paid=False):
    if student_exists(email, phone, rollno):
        return None  # Prevent duplicate entries

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO students (name, email, phone, rollno, interested_events, attended_events, paid)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (name, email, phone, rollno, json.dumps(interested_events), json.dumps(attended_events), paid)
    )
    student_id = cur.lastrowid
    conn.commit()
    cur.close()
    conn.close()
    return student_id

def get_student_by_id(student_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cur.fetchone()
    cur.close()
    conn.close()
    return dict(student) if student else None

def get_students(search_query=None, filter_paid=None):
    conn = get_db_connection()
    cur = conn.cursor()
    base_query = "SELECT * FROM students"
    params = []
    conditions = []
    
    if search_query:
        conditions.append("(LOWER(name) LIKE ? OR LOWER(email) LIKE ? OR LOWER(rollno) LIKE ?)")
        params.extend([f"%{search_query.lower()}%", f"%{search_query.lower()}%", f"%{search_query.lower()}%"])
    
    if filter_paid == "paid":
        conditions.append("paid = TRUE")
    elif filter_paid == "not-paid":
        conditions.append("paid = FALSE")
    
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    cur.execute(base_query, params)
    students = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in students]

def update_student(student_id, name, email, phone, rollno, interested_events, attended_events, paid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE students
        SET name=?, email=?, phone=?, rollno=?, interested_events=?, attended_events=?, paid=?
        WHERE id=?
        """,
        (name, email, phone, rollno, json.dumps(interested_events), json.dumps(attended_events), paid, student_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_student(student_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    cur.close()
    conn.close()

def check_admin_password(password):
    return password == "admin123"  # Replace with secure hashing if needed

if __name__ == "__main__":
    init_db()
