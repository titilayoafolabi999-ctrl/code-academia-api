from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional

app = FastAPI()

# 🛡 Enable CORS so your front-end can access the server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# 🔐 In-memory databases
users_db: Dict[str, dict] = {}
progress_db: Dict[str, dict] = {}
valid_codes = {
    "V9L2QM": False, "T7PK6X": False, "F8B1ZR": False, "J6W8NC": False,
    "Q4XYM2": False, "L3MK9P": False, "Z2ND7B": False, "M5RYXP": False,
    "K9X4JH": False, "A7TBQL": False
}

# 📦 Models
class Account(BaseModel):
    username: str
    email: str
    password: str
    referral_code: Optional[str] = None

class Login(BaseModel):
    email: str
    password: str

class Progress(BaseModel):
    email: str
    course: str
    week: int
    unlocked: bool

# ✨ Endpoints
@app.post("/create_account")
def create_account(data: Account):
    if data.email in users_db:
        return {"error": "Email already registered"}
    users_db[data.email] = data.dict()
    return {"status": "Account created"}

@app.post("/login")
def login(data: Login):
    user = users_db.get(data.email)
    if user and user["password"] == data.password:
        return {"status": "Login successful", "username": user["username"]}
    return {"error": "Invalid email or password"}

@app.post("/progress")
def update_progress(data: Progress):
    progress_db[data.email] = data.dict()
    return {"status": "Progress updated"}

@app.get("/progress/{email}")
def get_progress(email: str):
    return progress_db.get(email, {"error": "User not found"})

@app.get("/verify_code/{code}")
def verify_code(code: str):
    code = code.upper().strip()
    if code in valid_codes:
        if not valid_codes[code]:
            valid_codes[code] = True
            return {"status": "Code accepted"}
        else:
            return {"error": "Code already used"}
    return {"error": "Invalid code"}
