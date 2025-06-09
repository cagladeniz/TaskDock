import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, url_for
import requests
from datetime import date
from collections import defaultdict, Counter

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

API_URL = "http://backend:5001"

@app.context_processor
def inject_user():
    user_id = session.get("user_id")
    if user_id:
        try:
            user = requests.get(f"{API_URL}/api/user/{user_id}").json()
            return dict(user=user)
        except:
            return dict(user=None)
    return dict(user=None)

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    user = requests.get(f"{API_URL}/api/user/{session['user_id']}").json()
    all_tasks = requests.get(f"{API_URL}/api/tasks/{session['user_id']}").json()

    grouped_tasks = defaultdict(list)
    for task in all_tasks:
        cat = task["category"] if task["category"] else "Uncategorized"
        grouped_tasks[cat].append(task)

    status_count = Counter(t["status"] for t in all_tasks)
    stats = {
        "total": len(all_tasks),
        "completed": status_count.get("Completed", 0),
        "pending": status_count.get("Pending", 0),
        "inprogress": status_count.get("In Progress", 0)
    }
    return render_template("home.html", grouped_tasks=grouped_tasks, current_date=date.today().isoformat(), stats=stats)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            res = requests.post(f"{API_URL}/api/login", json={"email": email, "password": password})
            if res.status_code == 200:
                session["user_id"] = res.json()["user_id"]
                return redirect("/")
            else:
                error = "Invalid credentials"
        except:
            error = "Backend connection error"
        return render_template("login.html", error=error, hide_sidebar=True, hide_navbar=True)
    return render_template("login.html", hide_sidebar=True, hide_navbar=True)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        email = request.form["email"]
        password = request.form["password"]
        try:
            res = requests.post(f"{API_URL}/api/register", json={
                "name": name,
                "surname": surname,
                "email": email,
                "password": password
            })
            if res.status_code in [200, 201]:
                return redirect("/login")
            else:
                error = res.json().get("error", "Registration failed")
        except:
            error = "Backend connection error"
        return render_template("register.html", error=error, hide_sidebar=True, hide_navbar=True)
    return render_template("register.html", hide_sidebar=True, hide_navbar=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/add", methods=["GET", "POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        task = {
            "title": request.form["title"],
            "description": request.form["description"],
            "status": request.form["status"],
            "category": request.form["category"],
            "due_date": request.form["due_date"]
        }
        requests.post(f"{API_URL}/api/tasks/{session['user_id']}", json=task)
        return redirect("/")
    return render_template("add.html")

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        updated_task = {
            "title": request.form["title"],
            "description": request.form["description"],
            "status": request.form["status"],
            "category": request.form["category"],
            "due_date": request.form["due_date"]
        }
        requests.put(f"{API_URL}/api/task/{task_id}", json=updated_task)
        return redirect("/")
    task = requests.get(f"{API_URL}/api/task/{task_id}").json()
    return render_template("edit.html", task=task)

@app.route("/delete/<int:task_id>")
def delete(task_id):
    if "user_id" not in session:
        return redirect("/login")
    requests.delete(f"{API_URL}/api/task/{task_id}")
    return redirect("/")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        file = request.files.get("profile_pic")
        filename = None
        if file and allowed_file(file.filename):
            filename = f"user_{session['user_id']}_{secure_filename(file.filename)}"
            file.save(os.path.join("frontend", app.config['UPLOAD_FOLDER'], filename))
        payload = {"name": name, "surname": surname}
        if filename:
            payload["image"] = filename
        requests.put(f"{API_URL}/api/user/{session['user_id']}/update", json=payload)
    user = requests.get(f"{API_URL}/api/user/{session['user_id']}").json()
    stats = requests.get(f"{API_URL}/api/user/{session['user_id']}/stats").json()
    return render_template("profile.html", user=user, **stats)

@app.route("/categories", methods=["GET"])
def manage_categories():
    if "user_id" not in session:
        return redirect("/login")
    response = requests.get(f"{API_URL}/api/tasks/{session['user_id']}")
    tasks = response.json()
    unique_categories = sorted(set(t["category"] for t in tasks))
    return render_template("manage_categories.html", categories=unique_categories)


@app.route("/categories/rename", methods=["POST"])
def rename_category():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    old = request.form.get("old_name")
    new = request.form.get("new_name")
    requests.put(f"{API_URL}/api/categories/rename", json={
        "user_id": user_id,
        "old_name": old,
        "new_name": new
    })
    return redirect("/categories")

@app.route("/categories/delete", methods=["POST"])
def delete_category():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    name = request.form.get("name")
    requests.put(f"{API_URL}/api/categories/delete", json={
        "user_id": user_id,
        "name": name
    })
    return redirect("/categories")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
