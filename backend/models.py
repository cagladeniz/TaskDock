import sqlite3
import hashlib

def init_db():
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT,
            group_name TEXT,
            category TEXT,
            due_date TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email, password):
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, hash_password(password)))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True

def authenticate_user(email, password):
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=? AND password_hash=?", (email, hash_password(password)))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_tasks_by_user(user_id):
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id=?", (user_id,))
    tasks = [{
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "status": row[3],
        "group": row[4],
        "category": row[5],
        "due_date": row[6],
        "user_id": row[7]
    } for row in cur.fetchall()]
    conn.close()
    return tasks

def get_task_by_id(task_id):
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "status": row[3],
            "group": row[4],
            "category": row[5],
            "due_date": row[6],
            "user_id": row[7]
        }
    return None

def add_task(title, description, status, group, category, due_date, user_id):
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, description, status, group_name, category, due_date, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, description, status, group, category, due_date, user_id)
    )
    conn.commit()
    conn.close()

def update_task(task_id, title, description, status, group, category, due_date):
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET title=?, description=?, status=?, group_name=?, category=?, due_date=? WHERE id=?",
        (title, description, status, group, category, due_date, task_id)
    )
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    