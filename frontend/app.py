from flask import Flask, render_template, request, redirect, session, url_for
import requests
from datetime import date

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Güvenli oturum yönetimi için gerekli

API_URL = "http://backend:5001"

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    all_tasks = requests.get(f"{API_URL}/api/tasks/{session['user_id']}").json()

    status = request.args.get("status")
    category = request.args.get("category")
    due_before = request.args.get("due_before")

    filtered = all_tasks
    if status:
        filtered = [t for t in filtered if t["status"] == status]
    if category:
        filtered = [t for t in filtered if category.lower() in t["category"].lower()]
    if due_before:
        filtered = [t for t in filtered if t["due_date"] and t["due_date"] <= due_before]

    return render_template("home.html", tasks=filtered, current_date=date.today().isoformat())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            res = requests.post("http://backend:5001/api/login", json={"email": email, "password": password})
            if res.status_code == 200:
                user_id = res.json()["user_id"]
                session["user_id"] = user_id
                return redirect("/")
            else:
                error = "Invalid credentials"
        except Exception as e:
            error = "Backend connection error"
        return render_template("login.html", error=error, hide_sidebar=True, hide_navbar=True)
    
    return render_template("login.html", hide_sidebar=True, hide_navbar=True)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            res = requests.post("http://backend:5001/api/register", json={"email": email, "password": password})
            if res.status_code == 200:
                return redirect("/login")
            else:
                error = res.json().get("error", "Registration failed")
        except Exception:
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
            "group": request.form["group"],
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
        task = {
            "title": request.form["title"],
            "description": request.form["description"],
            "status": request.form["status"],
            "group": request.form["group"],
            "category": request.form["category"],
            "due_date": request.form["due_date"]
        }
        requests.put(f"{API_URL}/api/task/{task_id}", json=task)
        return redirect("/")
    task = requests.get(f"{API_URL}/api/task/{task_id}").json()
    return render_template("edit.html", task=task)

@app.route("/delete/<int:task_id>")
def delete(task_id):
    if "user_id" not in session:
        return redirect("/login")
    requests.delete(f"{API_URL}/api/task/{task_id}")
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
