from flask import Flask, request, jsonify
from models import (
    init_db, get_all_tasks, add_task,
    delete_task, update_task, get_task_by_id
)

app = Flask(__name__)
init_db()

@app.route("/api/tasks", methods=["GET", "POST"])
def tasks():
    if request.method == "POST":
        data = request.get_json()
        add_task(data["title"], data.get("description", ""), data.get("status", "Pending"))
        return jsonify({"message": "Task added"}), 201
    return jsonify(get_all_tasks())

@app.route("/api/tasks/<int:task_id>", methods=["GET", "PUT", "DELETE"])
def task_by_id(task_id):
    if request.method == "GET":
        task = get_task_by_id(task_id)
        if task:
            return jsonify(task)
        return jsonify({"error": "Not found"}), 404
    elif request.method == "PUT":
        data = request.get_json()
        update_task(task_id, data["title"], data.get("description", ""), data.get("status", "Pending"))
        return jsonify({"message": "Task updated"}), 200
    elif request.method == "DELETE":
        delete_task(task_id)
        return jsonify({"message": "Task deleted"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
