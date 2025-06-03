from flask import Flask, request, jsonify
from models import (
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
    success = create_user(data["email"], data["password"])
    return jsonify({"success": success}), 201 if success else 400

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
            data.get("group", ""),
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
            data.get("group", ""),
            data.get("category", ""),
            data.get("due_date", "")
        )
        return jsonify({"message": "Task updated"}), 200
    elif request.method == "DELETE":
        delete_task(task_id)
        return jsonify({"message": "Task deleted"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
    