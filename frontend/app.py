import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, url_for
import requests
from datetime import date
from collections import defaultdict, Counter

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

API_URL = "https://backend-white-dream-6506.fly.dev"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_user():
    user_id = session.get("user_id")
    user = None
    notifications = []
    if user_id:
        try:
            user = requests.get(f"{API_URL}/api/user/{user_id}").json()
            tasks = requests.get(f"{API_URL}/api/tasks/{user_id}").json()
            today = date.today().isoformat()
            for task in tasks:
                due = task.get("due_date")
                if due:
                    if due == today:
                        notifications.append(f"'{task['title']}' is due today!")
                    elif due < today:
                        notifications.append(f"'{task['title']}' is overdue!")
        except:
            pass
    return dict(user=user, notifications=notifications)

@app.route('/')
def index():
    if "user_id" in session:
        return redirect("/home")
    return render_template('index.html', hide_sidebar=True, hide_navbar=True)

@app.route('/home')
def home():
    if "user_id" not in session:
        return redirect("/login")

    all_tasks = requests.get(f"{API_URL}/api/tasks/{session['user_id']}").json()
    status_filter = request.args.get("status")
    category_filter = request.args.get("category")
    due_before = request.args.get("due_before")
    today = date.today().isoformat()
    filtered_tasks = []
    grouped_tasks = defaultdict(list)
    completed = pending = inprogress = overdue = 0

    for task in all_tasks:
        is_overdue = (
            task.get("due_date") and
            task["due_date"] < today and
            task["status"] in ["Pending", "In Progress"]
        )
        task["is_overdue"] = is_overdue

        if is_overdue and status_filter:
            overdue += 1
            continue

        if status_filter and task["status"] != status_filter:
            continue

        if category_filter and (task["category"] or "") != category_filter:
            continue

        if due_before and task["due_date"] and task["due_date"] > due_before:
            continue

        if is_overdue:
            overdue += 1
        elif task["status"] == "Completed":
            completed += 1
        elif task["status"] == "Pending":
            pending += 1
        elif task["status"] == "In Progress":
            inprogress += 1

        filtered_tasks.append(task)
        cat = task["category"] if task["category"] else "Uncategorized"
        grouped_tasks[cat].append(task)

    stats = {
        "total": len(filtered_tasks),
        "completed": completed,
        "pending": pending,
        "inprogress": inprogress,
        "overdue": overdue
    }
    response = requests.get(f"{API_URL}/api/categories/{session['user_id']}")
    unique_categories = response.json()
    return render_template("home.html", grouped_tasks=grouped_tasks, current_date=today, stats=stats, categories=unique_categories)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            res = requests.post(f"{API_URL}/api/login", json={"email": email, "password": password})
            if res.status_code == 200:
                session["user_id"] = res.json()["user_id"]
                return redirect("/home")
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
    response = requests.get(f"{API_URL}/api/categories/{session['user_id']}")
    unique_categories = response.json()
    if request.method == "POST":
        task = {
            "title": request.form["title"],
            "description": request.form["description"],
            "status": request.form["status"],
            "category": request.form["category"],
            "due_date": request.form["due_date"]
        }
        requests.post(f"{API_URL}/api/tasks/{session['user_id']}", json=task)
        return redirect("/home")
    return render_template("add.html", categories=unique_categories)

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    if "user_id" not in session:
        return redirect("/login")
    response = requests.get(f"{API_URL}/api/categories/{session['user_id']}")
    unique_categories = response.json()
    if request.method == "POST":
        updated_task = {
            "title": request.form["title"],
            "description": request.form["description"],
            "status": request.form["status"],
            "category": request.form["category"],
            "due_date": request.form["due_date"]
        }
        requests.put(f"{API_URL}/api/task/{task_id}", json=updated_task)
        return redirect("/home")
    task = requests.get(f"{API_URL}/api/task/{task_id}").json()
    return render_template("edit.html", task=task, categories=unique_categories)

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
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
        payload = {"name": name, "surname": surname}
        if filename:
            payload["image"] = filename
        requests.put(f"{API_URL}/api/user/{session['user_id']}/update", json=payload)
    user = requests.get(f"{API_URL}/api/user/{session['user_id']}").json()
    stats = requests.get(f"{API_URL}/api/user/{session['user_id']}/stats").json()
    return render_template("profile.html", user=user, **stats)

@app.route("/categories")
def manage_categories():
    if "user_id" not in session:
        return redirect("/login")
    response = requests.get(f"{API_URL}/api/categories/{session['user_id']}")
    categories = response.json()
    return render_template("manage_categories.html", categories=categories)

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
    name = request.form.get("name")
    user_id = session.get("user_id")
    response = requests.put(f"{API_URL}/api/categories/delete", json={
        "user_id": user_id,
        "name": name
    })
    return redirect("/categories")

@app.route("/categories/add", methods=["POST"])
def add_category():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    new_category = request.form.get("new_category")
    if new_category:
        requests.post(f"{API_URL}/api/categories/add", json={
            "user_id": user_id,
            "category": new_category
        })
    return redirect("/categories")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
