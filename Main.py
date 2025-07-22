from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import random, string, smtplib, requests
from email.mime.text import MIMEText
from datetime import datetime

app = FastAPI()

# 🌍 Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# 🔐 Admin account
admin_account = {
    "email": "titilayoafolabi999@gmail.com",
    "username": "Titilayo999",
    "password": "TitilayoAfolabi"
}

# 📦 In-memory databases
users_db: Dict[str, dict] = {
    "titilayoafolabi999@gmail.com": {
        "username": "Titilayo999",
        "email": "titilayoafolabi999@gmail.com",
        "password": "TitilayoAfolabi",
        "referral_code": None,
        "email_verified": True,
        "joined": "admin",
        "referrals": [],
        "created": str(datetime.now())
    }
}
progress_db: Dict[str, dict] = {}
valid_codes: Dict[str, dict] = {}
update_mode = {"status": False}
broadcast_feed: List[dict] = []

# 📧 Gmail sender
def send_email(to_email, code):
    msg = MIMEText(f"""
    <html>
      <body style="font-family:sans-serif;">
        <h2>Welcome to CODE ACADEMIA 🎓</h2>
        <p>Your unlock code is:</p>
        <div style="background:#f9f9f9;padding:10px;border:1px solid #ccc;">
          <h1>{code}</h1>
        </div>
        <p style="font-size:0.9em;color:#666;">This is an automated message from <b>CODE ACADEMIA</b>. Do not reply.</p>
      </body>
    </html>
    """, "html")
    msg["Subject"] = "Your CODE ACADEMIA Access Code"
    msg["From"] = "no-reply@codeacademia.com"
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(admin_account["email"], admin_account["password"])
        server.send_message(msg)

# 🧾 Models
class Account(BaseModel):
    username: str
    email: str
    password: str
    referral_code: Optional[str] = None
    email_verified: bool = False

class Login(BaseModel):
    email: str
    password: str

class Progress(BaseModel):
    email: str
    course: str
    week: int
    unlocked: bool

class BroadcastMessage(BaseModel):
    title: str
    body: str

# 👤 Signup
@app.post("/create_account")
def create_account(data: Account):
    if data.email in users_db:
        return {"error": "Email already registered"}
    users_db[data.email] = {
        "username": data.username,
        "email": data.email,
        "password": data.password,
        "referral_code": data.referral_code,
        "email_verified": data.email_verified,
        "joined": "manual",
        "referrals": [],
        "created": str(datetime.now())
    }
    return {"status": "Account created"}

# 🔐 Login
@app.post("/login")
def login(data: Login):
    user = users_db.get(data.email)
    if user and user["password"] == data.password:
        return {"status": "Login successful", "username": user["username"]}
    return {"error": "Invalid email or password"}

# 📈 Progress
@app.post("/progress")
def update_progress(data: Progress):
    progress_db[data.email] = data.dict()
    return {"status": "Progress updated"}

@app.get("/progress/{email}")
def get_progress(email: str):
    return progress_db.get(email, {"error": "User not found"})

# 🔓 Generate unlock code (expires in 10 minutes)
@app.get("/generate_code")
def generate_code():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    valid_codes[code] = {
        "used": False,
        "created": datetime.now()
    }
    return {"code": code}

@app.get("/verify_code/{code}")
def verify_code(code: str):
    code = code.upper().strip()
    data = valid_codes.get(code)
    if not data:
        return {"error": "Invalid code"}
    if data["used"]:
        return {"error": "Code already used"}
    if (datetime.now() - data["created"]).total_seconds() > 600:
        return {"error": "Code expired"}
    data["used"] = True
    return {"status": "Code accepted"}

# 🔧 Update toggle
@app.get("/toggle_update")
def toggle_update():
    update_mode["status"] = not update_mode["status"]
    return {"update_in_progress": update_mode["status"]}

@app.get("/status")
def get_status():
    return {"update_in_progress": update_mode["status"]}

# 🛠 Admin approval (secure)
@app.post("/admin/approve_payment")
def approve_payment(student_email: str = Form(...), admin_password: str = Form(...)):
    if admin_password != admin_account["password"]:
        return {"error": "Invalid admin password"}
    if student_email not in users_db:
        return {"error": "Student not found"}

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    valid_codes[code] = {
        "used": False,
        "created": datetime.now()
    }
    send_email(student_email, code)
    return {"status": f"Code sent to {student_email}", "code": code}

# 🧍 Admin tools
@app.get("/admin/user_count")
def user_count():
    return {"total_users": len(users_db)}

@app.get("/admin/user_profile/{email}")
def user_profile(email: str):
    user = users_db.get(email)
    if not user:
        return {"error": "User not found"}
    progress = progress_db.get(email, {})
    return {
        "profile": {
            "username": user["username"],
            "email": user["email"],
            "email_verified": user["email_verified"],
            "referral_code": user["referral_code"],
            "referrals": user["referrals"],
            "joined_via": user["joined"],
            "created": user["created"]
        },
        "progress": progress
    }

@app.get("/admin/all_users")
def all_users():
    return {"users": list(users_db.values())}

@app.get("/admin/search_username/{username}")
def search_username(username: str):
    results = [u for u in users_db.values() if u["username"].lower() == username.lower()]
    return {"results": results or "No matching users"}

@app.get("/admin/top_referrers")
def top_referrers():
    leaderboard = sorted(
        users_db.values(),
        key=lambda u: len(u.get("referrals", [])),
        reverse=True
    )
    return {"leaderboard": leaderboard[:10]}

@app.delete("/admin/delete_user/{email}")
def delete_user(email: str):
    if email in users_db:
        del users_db[email]
        progress_db.pop(email, None)
        return {"status": f"{email} deleted"}
    return {"error": "User not found"}

@app.get("/admin/export_users")
def export_users():
    return {"data": users_db}

# 📢 Social feed
@app.post("/admin/broadcast_message")
def broadcast_message(data: BroadcastMessage):
    entry = {
        "title": data.title,
        "body": data.body,
        "posted_at": str(datetime.now())
    }
    broadcast_feed.append(entry)
    return {"status": "Message posted"}

@app.get("/social_feed")
def social_feed():
    return {"feed": broadcast_feed[::-1]}
