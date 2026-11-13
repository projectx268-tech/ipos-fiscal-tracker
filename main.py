from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, timedelta
from typing import List
import hashlib

import models
import schemas
from database import engine, get_db, SessionLocal

# 1. ሁሉንም ቴብሎች (users ን ጨምሮ) በPostgreSQL መፍጠር
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="IPOS Fiscal Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. የይለፍ ቃል መቆለፊያ (Password Hashing Function)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# 3. ሰርቨሩ ሲነሳ ዋናው Admin በዳታቤዝ ውስጥ ከሌለ በራሱ እንዲፈጥር ማድረግ
@app.on_event("startup")
def create_default_admin():
    db = SessionLocal()
    try:
        admin_exists = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_exists:
            default_admin = models.User(
                username="admin",
                full_name="IPOS Administrator",
                password_hash=hash_password("ipos2026"),
                role="አስተዳዳሪ (Admin)"
            )
            db.add(default_admin)
            db.commit()
    finally:
        db.close()

# ==================== SCHEMAS FOR AUTH & USERS ====================

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    full_name: str
    password: str
    role: str = "ቴክኒሻን (Technician)"

# ==================== ROUTES / ENDPOINTS ====================

@app.get("/")
def serve_frontend():
    return FileResponse("ipos_tracker.html")

# ሀ. ከPostgreSQL ዳታቤዝ እያረጋገጠ የሚያስገባ Login API
@app.post("/api/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == data.username.strip().lower(),
        models.User.is_active == True
    ).first()

    if not user or user.password_hash != hash_password(data.password):
        raise HTTPException(status_code=401, detail="የተሳሳተ የተጠቃሚ ስም ወይም የይለፍ ቃል!")

    return {
        "message": "Success",
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role
    }

# ለ. አዲስ ቴክኒሻን ወይም ተጠቃሚ ወደ ዳታቤዝ መመዝገቢያ API
@app.post("/api/users")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user_data.username.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="ይህ የተጠቃሚ ስም (Username) ቀድሞ ተመዝግቧል!")

    new_user = models.User(
        username=user_data.username.strip().lower(),
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    return {"message": f"ተጠቃሚ '{new_user.username}' በተሳካ ሁኔታ ተመዝግቧል!"}

# ሐ. ሁሉንም ማሽኖች ከነ ቀነ-ገደባቸው የሚያወጣ API
@app.get("/api/machines", response_model=List[schemas.MachineResponse])
def get_machines(db: Session = Depends(get_db)):
    records = db.query(
        models.JobCard, models.Machine, models.Client
    ).join(
        models.Machine, models.JobCard.machine_id == models.Machine.id
    ).join(
        models.Client, models.JobCard.client_id == models.Client.id
    ).order_by(models.JobCard.received_date.desc()).all()

    today = date.today()
    response = []

    for jc, m, c in records:
        due_date = m.next_renewal_due_date
        days_left = (due_date - today).days

        response.append({
            "id": jc.job_card_number,
            "clientName": c.company_name,
            "tin": c.tin_number,
            "phone": c.phone_number,
            "model": m.model_name,
            "serial": m.serial_number,
            "mrc": m.mrc_number or "",
            "entryDate": str(jc.received_date.date()) if jc.received_date else "",
            "lastRenewalDate": str(m.last_annual_renewal_date),
            "dueDate": str(due_date),
            "daysLeft": days_left,
            "problem": jc.reported_problem,
            "status": jc.status
        })

    return response

# መ. አዲስ ማሽን እና Job Card መመዝገቢያ API
@app.post("/api/machines/check-in")
def check_in_machine(data: schemas.MachineCheckIn, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.tin_number == data.tin).first()
    if not client:
        client = models.Client(
            company_name=data.client_name,
            tin_number=data.tin,
            phone_number=data.phone
        )
        db.add(client)
        db.flush()

    next_due = data.last_renewal_date + timedelta(days=365)

    machine = db.query(models.Machine).filter(models.Machine.serial_number == data.serial).first()
    if not machine:
        machine = models.Machine(
            client_id=client.id,
            model_name=data.model,
            serial_number=data.serial,
            mrc_number=data.mrc,
            last_annual_renewal_date=data.last_renewal_date,
            next_renewal_due_date=next_due
        )
        db.add(machine)
        db.flush()
    else:
        machine.last_annual_renewal_date = data.last_renewal_date
        machine.next_renewal_due_date = next_due

    total_jobs = db.query(models.JobCard).count() + 1
    jc_number = f"IPOS-JC-2026-{total_jobs:04d}"

    job_card = models.JobCard(
        job_card_number=jc_number,
        machine_id=machine.id,
        client_id=client.id,
        reported_problem=data.problem,
        status="በጥገና ላይ"
    )
    db.add(job_card)
    db.commit()

    return {"message": "Success", "job_card_number": jc_number}
# ሠ. የተመዘገበ መረጃ ማስተካከያ (Edit / Update API)
@app.put("/api/machines/{job_card_number}")
def update_machine_record(job_card_number: str, data: schemas.MachineUpdate, db: Session = Depends(get_db)):
    jc = db.query(models.JobCard).filter(models.JobCard.job_card_number == job_card_number).first()
    if not jc:
        raise HTTPException(status_code=404, detail="Job Card አልተገኘም!")

    machine = db.query(models.Machine).filter(models.Machine.id == jc.machine_id).first()
    client = db.query(models.Client).filter(models.Client.id == jc.client_id).first()

    # 1. የደንበኛ መረጃ ማስተካከል
    if client:
        client.company_name = data.client_name
        client.tin_number = data.tin
        client.phone_number = data.phone

    # 2. የማሽን እና የ365 ቀን እድሳት መረጃ ማስተካከል
    if machine:
        machine.model_name = data.model
        machine.serial_number = data.serial
        machine.mrc_number = data.mrc
        machine.last_annual_renewal_date = data.last_renewal_date
        machine.next_renewal_due_date = data.last_renewal_date + timedelta(days=365)

    # 3. የJob Card ችግር እና ሁኔታ (Status) ማስተካከል
    jc.reported_problem = data.problem
    jc.status = data.status

    db.commit()
    return {"message": "መረጃው በተሳካ ሁኔታ ተስተካክሏል!"}

# ረ. በስህተት የተመዘገበ መረጃ መሰረዣ (Delete API)
@app.delete("/api/machines/{job_card_number}")
def delete_machine_record(job_card_number: str, db: Session = Depends(get_db)):
    jc = db.query(models.JobCard).filter(models.JobCard.job_card_number == job_card_number).first()
    if not jc:
        raise HTTPException(status_code=404, detail="Job Card አልተገኘም!")

    db.delete(jc)
    db.commit()
    return {"message": "መረጃው በተሳካ ሁኔታ ተሰርዟል!"}