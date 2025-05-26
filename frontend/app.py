from flask import Flask, render_template, request, redirect
import requests

app = Flask(__name__)
API_URL = "http://backend:5001/api/tasks"

def fetch_tasks_by_status(status):
    all_tasks = requests.get(API_URL).json()
    return [task for task in all_tasks if task["status"] == status]

@app.route("/")
def home():
    tasks = requests.get(API_URL).json()
    return render_template("home.html", tasks=tasks, active="dashboard")

@app.route("/completed")
def completed():
    tasks = fetch_tasks_by_status("Completed")
    return render_template("home.html", tasks=tasks, active="completed")

@app.route("/pending")
def pending():
    tasks = fetch_tasks_by_status("Pending")
    return render_template("home.html", tasks=tasks, active="pending")

@app.route("/in-progress")
def in_progress():
    tasks = fetch_tasks_by_status("In Progress")
    return render_template("home.html", tasks=tasks, active="inprogress")

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        task = {
            "title": request.form["title"],
            "description": request.form["description"],
            "status": request.form["status"]
        }
        requests.post(API_URL, json=task)
        return redirect("/")
    return render_template("add.html", active="add")

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    if request.method == "POST":
        task = {
            "title": request.form["title"],
            "description": request.form["description"],
            "status": request.form["status"]
        }
        requests.put(f"{API_URL}/{task_id}", json=task)
        return redirect("/")
    task = requests.get(f"{API_URL}/{task_id}").json()
    return render_template("edit.html", task=task)

@app.route("/delete/<int:task_id>")
def delete(task_id):
    requests.delete(f"{API_URL}/{task_id}")
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
