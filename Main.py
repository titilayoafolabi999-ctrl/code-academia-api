# CODE ACADEMIA Backend v1.12 — SQLite + FastAPI
import sqlite3
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random, string

DB_NAME = "code_academia.db"
app = FastAPI()

# 🔓 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ⚙️ DB Utility
def query(sql, args=(), fetch=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(sql, args)
    result = cursor.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return result

# 🏁 Create tables from models.sql
@app.on_event("startup")
def init_db():
    with open("models.sql", "r") as f:
        for statement in f.read().split(";"):
            if statement.strip():
                query(statement)

# 👤 Create Account
@app.post("/create_account")
def create_account(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    existing = query("SELECT * FROM users WHERE email = ?", [email], True)
    if existing:
        return {"error": "Email already registered"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query("INSERT INTO users (username, email, password, role, created) VALUES (?, ?, ?, ?, ?)", [username, email, password, "student", now])
    return {"status": "Account created"}

# 🔑 Login
@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    user = query("SELECT username, role FROM users WHERE email = ? AND password = ?", [email, password], True)
    if not user:
        return {"error": "Invalid credentials"}
    return {"status": "Login successful", "username": user[0][0], "role": user[0][1]}

# 📚 Get Course
@app.get("/get_course/{name}")
def get_course(name: str):
    price = query("SELECT price FROM courses WHERE name = ?", [name], True)
    weeks = query("SELECT week, title, lesson FROM weeks WHERE course = ? ORDER BY week", [name], True)
    lessons = [dict(zip(["week", "title", "lesson"], w)) for w in weeks]
    return {"course": name, "price": price[0][0] if price else 0, "weeks": lessons}

# ✍️ Add Lesson
@app.post("/admin/add_lesson")
def add_lesson(
    course: str = Form(...),
    week: int = Form(...),
    title: str = Form(...),
    lesson: str = Form(...),
    admin_password: str = Form(...)
):
    if admin_password != "TitilayoAfolabi":
        return {"error": "Unauthorized"}
    query("INSERT INTO weeks (course, week, title, lesson) VALUES (?, ?, ?, ?)", [course, week, title, lesson])
    return {"status": f"Week {week} added to {course}"}

# 💰 Update Price
@app.post("/admin/update_price")
def update_price(
    course: str = Form(...),
    new_price: int = Form(...),
    admin_password: str = Form(...)
):
    if admin_password != "TitilayoAfolabi":
        return {"error": "Unauthorized"}
    query("UPDATE courses SET price = ? WHERE name = ?", [new_price, course])
    return {"status": f"Price for {course} updated to ₦{new_price}"}

# 📈 Student Progress
@app.post("/progress")
def update_progress(
    email: str = Form(...),
    course: str = Form(...),
    week: int = Form(...),
    passed_quiz: bool = Form(...)
):
    query("INSERT INTO progress (email, course, week, passed_quiz) VALUES (?, ?, ?, ?)", [email, course, week, passed_quiz])
    return {"status": "Progress saved"}

@app.get("/progress/{email}/{course}")
def get_progress(email: str, course: str):
    data = query("SELECT week, passed_quiz FROM progress WHERE email = ? AND course = ?", [email, course], True)
    return {"progress": [dict(zip(["week", "passed_quiz"], row)) for row in data]}

# 📝 Weekly Quiz
@app.get("/quiz/{course}/{week}")
def get_quiz(course: str, week: int):
    qdata = query("SELECT question, options, answer FROM quizzes WHERE course = ? AND week = ?", [course, week], True)
    return {"questions": [
        { "question": row[0], "options": row[1].split(","), "answer": row[2] } for row in qdata
    ]}

# 🔓 Unlock Codes
@app.get("/generate_code")
def generate_code():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query("INSERT INTO codes (code, used, created) VALUES (?, ?, ?)", [code, 0, now])
    return {"code": code}

@app.get("/verify_code/{code}")
def verify_code(code: str):
    info = query("SELECT used, created FROM codes WHERE code = ?", [code.strip().upper()], True)
    if not info:
        return {"error": "Invalid"}
    used, created = info[0]
    if used:
        return {"error": "Already used"}
    elapsed = (datetime.now() - datetime.strptime(created, "%Y-%m-%d %H:%M:%S")).total_seconds()
    if elapsed > 600:
        return {"error": "Code expired"}
    query("UPDATE codes SET used = 1 WHERE code = ?", [code])
    return {"status": "Code accepted"}
