#backend/routes/recruiters.py
from fastapi import APIRouter, HTTPException
from urllib.parse import unquote
from models import RecruiterRegistration
from database import recruiters_collection
from pydantic import BaseModel, EmailStr

router = APIRouter()

@router.post("/register")
async def register_recruiter(recruiter: RecruiterRegistration):
    """Register a new recruiter"""
    # Check if recruiter already exists
    existing_recruiter = recruiters_collection.find_one({"email": recruiter.email})
    if existing_recruiter:
        raise HTTPException(status_code=400, detail="Recruiter with this email already exists")
    
    # Fixed: Remove duplicate line
    recruiter_data = recruiter.model_dump()
    recruiter_data["jobs_posted"] = 0

    result = recruiters_collection.insert_one(recruiter_data)
    return {"message": "Recruiter registered successfully", "recruiter_id": str(result.inserted_id)}

@router.get("/profile/{email}")
async def get_recruiter_profile(email: str):
    """Get recruiter profile by email"""
    # Fixed: Decode URL-encoded email
    decoded_email = unquote(email)
    
    recruiter = recruiters_collection.find_one({"email": decoded_email})
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    
    recruiter["_id"] = str(recruiter["_id"])
    return recruiter

class RecruiterLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def login_recruiter(data: RecruiterLogin):
    recruiter = recruiters_collection.find_one({"email": data.email, "password": data.password})
    if not recruiter:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login successful", "email": recruiter["email"]}

@router.get("/verify/{email}")
async def verify_recruiter_exists(email: str):
    """Verify if recruiter exists without returning full profile"""
    # Fixed: Decode URL-encoded email
    decoded_email = unquote(email)
    
    recruiter = recruiters_collection.find_one({"email": decoded_email}, {"_id": 1})
    exists = recruiter is not None
    
    return {"exists": exists, "email": decoded_email}
