import sqlite3
import hashlib

def init_db():
    conn = sqlite3.connect("/data/tasks.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            surname TEXT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            image TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT,
            category TEXT,
            due_date TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(name, surname, email, password):
    conn = sqlite3.connect("/data/tasks.db")
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, surname, email, password_hash) VALUES (?, ?, ?, ?)",
            (name, surname, email, hash_password(password))
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True

def authenticate_user(email, password):
    conn = sqlite3.connect("/data/tasks.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=? AND password_hash=?", (email, hash_password(password)))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_tasks_by_user(user_id):
    conn = sqlite3.connect("/data/tasks.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id=?", (user_id,))
    tasks = [{
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "status": row[3],
        "category": row[5],
        "due_date": row[6],
        "user_id": row[7]
    } for row in cur.fetchall()]
    conn.close()
    return tasks

def get_task_by_id(task_id):
    conn = sqlite3.connect("/data/tasks.db")
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
            "category": row[5],
            "due_date": row[6],
            "user_id": row[7]
        }
    return None

def add_task(title, description, status, category, due_date, user_id):
    conn = sqlite3.connect("/data/tasks.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, description, status, category, due_date, user_id) VALUES (?, ?, ?, ?, ?, ?)",
        (title, description, status, category, due_date, user_id)
    )
    conn.commit()
    conn.close()

def update_task(task_id, title, description, status, category, due_date):
    conn = sqlite3.connect("/data/tasks.db")
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET title=?, description=?, status=?, category=?, due_date=? WHERE id=?",
        (title, description, status, category, due_date, task_id)
    )
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect("/data/tasks.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

def get_user_by_id(user_id):
    conn = sqlite3.connect("/data/tasks.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_task_stats(user_id):
    conn = sqlite3.connect("/data/tasks.db")
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,)).fetchone()[0]
    completed = cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'Completed'", (user_id,)).fetchone()[0]
    pending = cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'Pending'", (user_id,)).fetchone()[0]
    inprogress = cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'In Progress'", (user_id,)).fetchone()[0]
    conn.close()
    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "inprogress": inprogress
    }

def delete_category_for_user(user_id, name):
    conn = sqlite3.connect("/data/tasks.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM categories WHERE name = ? AND user_id = ?", (name, user_id))
    cur.execute("UPDATE tasks SET category = NULL WHERE category = ? AND user_id = ?", (name, user_id))
    conn.commit()
    conn.close()

def rename_category_for_user(user_id, old_name, new_name):
    conn = sqlite3.connect("/data/tasks.db")
    cur = conn.cursor()
    cur.execute("UPDATE categories SET name = ? WHERE name = ? AND user_id = ?", (new_name, old_name, user_id))
    cur.execute("UPDATE tasks SET category = ? WHERE category = ? AND user_id = ?", (new_name, old_name, user_id))
    conn.commit()
    conn.close()
