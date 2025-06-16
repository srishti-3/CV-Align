#backend/routes/cv.py
from fastapi import APIRouter, UploadFile, File, Form, Query
from utils.cloudinary_upload import upload_cv
from database import db
from models import JobDescription
from bson import ObjectId

router = APIRouter()

@router.post("/upload-job/")
async def upload_job(role: str = Form(...),):
    doc = {
        "role": role,
    }
    result = db.jobs.insert_one(doc)
    return {"job_id": str(result.inserted_id)}

@router.post("/upload-cv/")
async def upload_cv_file(file: UploadFile = File(...), name: str = Form(...), email: str = Form(...), job_id: str = Form(...)):
    cv_url = upload_cv(file)
    db.cvs.insert_one({
        "name": name,
        "email": email,
        "job_id": job_id,
        "cv_url": cv_url
    })
    return {"message": "CV uploaded successfully", "cv_url": cv_url}

@router.post("/upload-job-description-pdf/")
async def upload_job_description(file: UploadFile = File(...)):
    url = upload_cv(file)
    return {"pdf_url": url}

@router.get("/jobs/")
async def list_jobs():
    jobs = list(db.jobs.find())
    for job in jobs:
        job["_id"] = str(job["_id"])
    return jobs

@router.get("/applications/")
async def get_applications(job_id: str = Query(...)):
    applications = list(db.cvs.find({"job_id": job_id}))
    for app in applications:
        app["_id"] = str(app["_id"])
    return applications

@router.get("/cvs/")
async def get_cvs(email: str = Query(...)):
    cvs = list(db.cvs.find({"email": email}))
    for cv in cvs:
        cv["_id"] = str(cv["_id"])
    return cvs
