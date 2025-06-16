#backend/routes/students.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from models import StudentRegistration, StudentProfile, CVUpload, BaseModel, EmailStr
from database import students_collection, applications_collection, parsed_cv_collection
from utils.cloudinary_upload import upload_cv
from bson import ObjectId
from typing import List
import datetime

from .parsed_cv import parse_cv
from database import db
from models import JobApplication
import os
import requests
import re
from models import ParsedCV
from bson import json_util
import json


router = APIRouter()

@router.post("/register", response_model=dict)
async def register_student(student: StudentRegistration):
    """Register a new student"""
    # Check if student already exists
    existing_student = students_collection.find_one({"email": student.email})
    if existing_student:
        raise HTTPException(status_code=400, detail="Student with this email already exists")
    
    student_data = student.model_dump()
    student_data["cv_count"] = 0
    student_data["cvs"] = []
    
    result = students_collection.insert_one(student_data)
    return {"message": "Student registered successfully", "student_id": str(result.inserted_id)}

class StudentLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def login_recruiter(data: StudentLogin):
    student = students_collection.find_one({"email": data.email, "password": data.password})
    if not student:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login successful", "email": student["email"]}

@router.get("/profile/{email}")
async def get_student_profile(email: str):
    """Fetch student profile by email"""
    student = students_collection.find_one({"email": email})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Serialize all ObjectIds safely
    json_compatible = json.loads(json_util.dumps(student))
    return json_compatible

@router.post("/upload-cv/{email}")
async def upload_student_cv(
    email: str,
    file: UploadFile = File(...),
    cv_name: str = Form(...)
):
    """Upload CV for a student (max 3 CVs)"""
    # Check if student exists
    student = students_collection.find_one({"email": email})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check CV limit
    if student.get("cv_count", 0) >= 3:
        raise HTTPException(status_code=400, detail="Maximum 3 CVs allowed per student")
    
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
    
    try:
        # Upload to Cloudinary
        cv_url = upload_cv(file)
        
        # Create CV record
        cv_data = {
            "_id": ObjectId(),
            "cv_name": cv_name,
            "cv_url": cv_url
        }
        
        # Update student record
        students_collection.update_one(
            {"email": email},
            {
                "$push": {"cvs": cv_data},
                "$inc": {"cv_count": 1}
            }
        )
        
        return {
            "message": "CV uploaded successfully",
            "cv_id": str(cv_data["_id"]),
            "cv_url": cv_url
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV upload failed: {str(e)}")

@router.get("/cvs/{email}")
async def get_student_cvs(email: str):
    """Get all CVs for a student"""
    student = students_collection.find_one({"email": email})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    cvs = student.get("cvs", [])
    for cv in cvs:
        cv["_id"] = str(cv["_id"])
    
    return {"cvs": cvs, "cv_count": len(cvs)}

@router.delete("/cvs/{email}/{cv_id}")
async def delete_student_cv(email: str, cv_id: str):
    """Delete a specific CV"""
    result = students_collection.update_one(
        {"email": email},
        {
            "$pull": {"cvs": {"_id": ObjectId(cv_id)}},
            "$inc": {"cv_count": -1}
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="CV not found")
    
    return {"message": "CV deleted successfully"}

@router.get("/applications/{email}")
async def get_student_applications(email: str):
    """Get all job applications for a student"""
    applications = list(applications_collection.find({"student_email": email}))
    for app in applications:
        app["_id"] = str(app["_id"])
    
    return {"applications": applications}

def download_cv(cv_url: str, save_path: str):
    response = requests.get(cv_url)
    with open(save_path, "wb") as f:
        f.write(response.content)


@router.post("/parse-all-cvs/")
async def parse_all_uploaded_cvs():
    parsed_results = []

    # Make sure the temp folder exists
    os.makedirs("temp_cvs", exist_ok=True)

    # Fetch all students with at least one CV
    students = list(students_collection.find({"cv_count": {"$gt": 0}}))
    #print(students)

    for student in students:
        email = student["email"]
        for cv in student.get("cvs", []):
            try:
                filename = f"{email.replace('@', '_at_')}_{str(cv['_id'])}.pdf"
                save_path = os.path.join("temp_cvs", filename)

                # Download the file
                download_cv(cv["cv_url"], save_path)

                # Parse it
                parsed = parse_cv(save_path)

                # Cleanup
                os.remove(save_path)

                # Update inside embedded array — tricky but doable
                parsed_doc = {
                    "_id": ObjectId(),  # optional, Mongo will auto-generate if omitted
                    "student_email": email,
                    "cv_id": cv["_id"],
                    "parsed": parsed
                }

                parsed_cv_collection.insert_one(parsed_doc)

                parsed_results.append({
                    "student_email": email,
                    "cv_id": str(cv["_id"]),
                    "parsed": parsed
                })

            except Exception as e:
                parsed_results.append({
                    "student_email": email,
                    "cv_id": str(cv.get("_id", "unknown")),
                    "error": str(e)
                })

    return {"total": len(parsed_results), "results": parsed_results}

async def get_all_parsed_cvs(student_email: str = Query(None)):
    query = {"student_email": student_email} if student_email else {}
    cvs = list(parsed_cv_collection.find(query, {"_id": 0}))
    return {"total": len(cvs), "data": cvs}
