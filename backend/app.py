import sqlite3
from flask import Flask, request, jsonify
from models import (
    get_user_by_id,
    get_user_task_stats,
    init_db,
    get_tasks_by_user,
    get_task_by_id,
    add_task,
    update_task,
    delete_task,
    create_user,
    authenticate_user )

app = Flask(__name__)
init_db()

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    success = create_user(
        data["name"],
        data["surname"],
        data["email"],
        data["password"]
    )
    return jsonify({"success": success}), 201 if success else 400

@app.route("/api/user/<int:user_id>/update", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    fields = ["name", "surname"]
    values = [data["name"], data["surname"]]

    if "image" in data:
        fields.append("image")
        values.append(data["image"])

    values.append(user_id)
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    cur.execute(f"UPDATE users SET {', '.join(f + ' = ?' for f in fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    user_id = authenticate_user(data["email"], data["password"])
    if user_id:
        return jsonify({"user_id": user_id}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/tasks/<int:user_id>", methods=["GET", "POST"])
def user_tasks(user_id):
    if request.method == "POST":
        data = request.get_json()
        add_task(
            data["title"],
            data.get("description", ""),
            data.get("status", "Pending"),
            data.get("category", ""),
            data.get("due_date", ""),
            user_id
        )
        return jsonify({"message": "Task added"}), 201
    return jsonify(get_tasks_by_user(user_id))

@app.route("/api/task/<int:task_id>", methods=["GET", "PUT", "DELETE"])
def task_by_id(task_id):
    if request.method == "GET":
        task = get_task_by_id(task_id)
        return jsonify(task)
    elif request.method == "PUT":
        data = request.get_json()
        update_task(
            task_id,
            data["title"],
            data.get("description", ""),
            data.get("status", "Pending"),
            data.get("category", ""),
            data.get("due_date", "")
        )
        return jsonify({"message": "Task updated"}), 200
    elif request.method == "DELETE":
        delete_task(task_id)
        return jsonify({"message": "Task deleted"}), 200
    
@app.route("/api/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = get_user_by_id(user_id)
    return jsonify(user)

@app.route("/api/user/<int:user_id>/stats", methods=["GET"])
def get_stats(user_id):
    stats = get_user_task_stats(user_id)
    return jsonify(stats)

@app.route("/api/categories/rename", methods=["PUT"])
def rename_category_api():
    data = request.get_json()
    user_id = data["user_id"]
    old = data["old_name"]
    new = data["new_name"]
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET category = ? WHERE user_id = ? AND category = ?", (new, user_id, old))
    conn.commit()
    conn.close()
    return jsonify({"message": "Renamed"}), 200

@app.route("/api/categories/delete", methods=["PUT"])
def delete_category_api():
    data = request.get_json()
    user_id = data["user_id"]
    name = data["name"]

    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET category = NULL WHERE user_id = ? AND category = ?", (user_id, name))
    conn.commit()
    conn.close()
    return jsonify({"message": "Deleted"}), 200

@app.route('/api/categories/add', methods=['POST'])
def add_category():
    data = request.get_json()
    user_id = data.get("user_id")
    category = data.get("category")
    if not user_id or not category:
        return jsonify({"error": "Missing user_id or category"}), 400
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM categories WHERE user_id = ? AND name = ?", (user_id, category))
    if cur.fetchone():
        conn.close()
        return jsonify({"message": "Category already exists"}), 200
    cur.execute("INSERT INTO categories (user_id, name) VALUES (?, ?)", (user_id, category))
    conn.commit()
    conn.close()
    return jsonify({"message": "Category added"}), 201

@app.route('/api/categories/<int:user_id>')
def get_categories(user_id):
    conn = sqlite3.connect("data/tasks.db")
    cur = conn.cursor()
    cur.execute("SELECT name FROM categories WHERE user_id = ?", (user_id,))
    results = [row[0] for row in cur.fetchall()]
    conn.close()
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
    