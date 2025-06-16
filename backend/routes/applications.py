#backend/routes/applications.py
from fastapi import APIRouter, HTTPException, Form
from models import JobApplication
from database import applications_collection, students_collection, jobs_collection
from bson import ObjectId
from typing import List, Optional
from urllib.parse import unquote
import datetime

router = APIRouter()

@router.post("/apply")
async def apply_for_job(
    student_email: str = Form(...),
    job_id: str = Form(...),
    cv_id: str = Form(...)
):
    """Apply for a job with a specific CV"""
    try:
        # Decode URL-encoded email
        decoded_email = unquote(student_email)
        
        # Verify student exists and get their CV
        student = students_collection.find_one({"email": decoded_email})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Find the specific CV
        selected_cv = None
        for cv in student.get("cvs", []):
            if str(cv["_id"]) == cv_id:
                selected_cv = cv
                break
        
        if not selected_cv:
            raise HTTPException(status_code=404, detail="CV not found")
        
        # Verify job exists and is active
        job = jobs_collection.find_one({"_id": ObjectId(job_id), "is_active": True})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or inactive")
        
        # Check if student has already applied for this job
        existing_application = applications_collection.find_one({
            "student_email": decoded_email,
            "job_id": job_id
        })
        if existing_application:
            raise HTTPException(status_code=400, detail="You have already applied for this job")
        
        # Create application
        application_data = {
            "student_email": decoded_email,
            "student_name": student.get("name", ""),
            "job_id": job_id,
            "job_title": job.get("title", ""),
            "company": job.get("company", ""),
            "cv_id": cv_id,
            "cv_name": selected_cv.get("cv_name", ""),
            "cv_url": selected_cv.get("cv_url", ""),
            "applied_at": datetime.datetime.now(datetime.timezone.utc),
            "status": "pending",
            "score": None,
            "feedback": None,
            "recruiter_email": job.get("recruiter_email", "")
        }
        
        result = applications_collection.insert_one(application_data)
        
        return {
            "message": "Application submitted successfully",
            "application_id": str(result.inserted_id)
        }
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Application failed: {str(e)}")

@router.get("/student/{student_email}")
async def get_student_applications(student_email: str):
    """Get all applications for a specific student"""
    # Decode URL-encoded email
    decoded_email = unquote(student_email)
    
    applications = list(applications_collection.find({"student_email": decoded_email}).sort("applied_at", -1))
    
    for app in applications:
        app["_id"] = str(app["_id"])
        app["applied_at"] = app["applied_at"].isoformat() if app.get("applied_at") else None
    
    return {"applications": applications}

@router.get("/job/{job_id}")
async def get_job_applications(job_id: str, recruiter_email: str):
    """Get all applications for a specific job (only for the recruiter who posted it)"""
    try:
        # Decode URL-encoded email
        decoded_email = unquote(recruiter_email)
        
        # Verify the job belongs to the recruiter
        job = jobs_collection.find_one({"_id": ObjectId(job_id), "recruiter_email": decoded_email})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or unauthorized")
        
        applications = list(applications_collection.find({"job_id": job_id}).sort("applied_at", -1))
        
        for app in applications:
            app["_id"] = str(app["_id"])
            app["applied_at"] = app["applied_at"].isoformat() if app.get("applied_at") else None
        
        return {
            "job_title": job.get("title", ""),
            "applications": applications,
            "total_applications": len(applications)
        }
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail="Invalid job ID")

@router.get("/recruiter/{recruiter_email}")
async def get_recruiter_applications(recruiter_email: str):
    """Get all applications for jobs posted by a specific recruiter"""
    # Decode URL-encoded email
    decoded_email = unquote(recruiter_email)
    
    # Get all jobs by this recruiter
    recruiter_jobs = list(jobs_collection.find({"recruiter_email": decoded_email}))
    job_ids = [str(job["_id"]) for job in recruiter_jobs]
    
    if not job_ids:
        return {"applications": [], "total_applications": 0}
    
    # Get all applications for these jobs
    applications = list(applications_collection.find({"job_id": {"$in": job_ids}}).sort("applied_at", -1))
    
    for app in applications:
        app["_id"] = str(app["_id"])
        app["applied_at"] = app["applied_at"].isoformat() if app.get("applied_at") else None
    
    return {
        "applications": applications,
        "total_applications": len(applications)
    }

@router.get("/analytics/recruiter/{recruiter_email}")
async def get_recruiter_analytics(recruiter_email: str):
    """Get analytics data for a specific recruiter's applications"""
    try:
        # Fixed: Decode URL-encoded email
        decoded_email = unquote(recruiter_email)
        
        # Get all jobs by this recruiter
        recruiter_jobs = list(jobs_collection.find({"recruiter_email": decoded_email}))
        job_ids = [str(job["_id"]) for job in recruiter_jobs]
        
        if not job_ids:
            return {
                "total_applications": 0,
                "total_jobs": 0,
                "status_breakdown": {
                    "pending": 0,
                    "reviewed": 0,
                    "shortlisted": 0,
                    "rejected": 0
                },
                "recent_applications": [],
                "top_jobs": []
            }
        
        # Get all applications for these jobs
        applications = list(applications_collection.find({"job_id": {"$in": job_ids}}))
        
        # Calculate status breakdown
        status_breakdown = {
            "pending": 0,
            "reviewed": 0,
            "shortlisted": 0,
            "rejected": 0
        }
        
        for app in applications:
            status = app.get("status", "pending")
            if status in status_breakdown:
                status_breakdown[status] += 1
        
        # Get recent applications (last 10)
        recent_applications = list(applications_collection.find(
            {"job_id": {"$in": job_ids}}
        ).sort("applied_at", -1).limit(10))
        
        for app in recent_applications:
            app["_id"] = str(app["_id"])
            app["applied_at"] = app["applied_at"].isoformat() if app.get("applied_at") else None
        
        # Get top jobs by application count
        job_application_counts = {}
        for app in applications:
            job_id = app["job_id"]
            if job_id not in job_application_counts:
                job_application_counts[job_id] = {
                    "job_id": job_id,
                    "job_title": app.get("job_title", "Unknown"),
                    "company": app.get("company", "Unknown"),
                    "count": 0
                }
            job_application_counts[job_id]["count"] += 1
        
        top_jobs = sorted(job_application_counts.values(), key=lambda x: x["count"], reverse=True)[:5]
        
        return {
            "total_applications": len(applications),
            "total_jobs": len(recruiter_jobs),
            "status_breakdown": status_breakdown,
            "recent_applications": recent_applications,
            "top_jobs": top_jobs
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.put("/{application_id}/status")
async def update_application_status(
    application_id: str,
    status: str = Form(...),
    recruiter_email: str = Form(...),
    score: Optional[float] = Form(None),
    feedback: Optional[str] = Form(None)
):
    """Update application status, score, and feedback (only by recruiter)"""
    try:
        # Decode URL-encoded email
        decoded_email = unquote(recruiter_email)
        
        # Verify application exists and belongs to recruiter's job
        application = applications_collection.find_one({"_id": ObjectId(application_id)})
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Verify the recruiter owns the job
        job = jobs_collection.find_one({
            "_id": ObjectId(application["job_id"]),
            "recruiter_email": decoded_email
        })
        if not job:
            raise HTTPException(status_code=403, detail="Unauthorized to update this application")
        
        # Validate status
        valid_statuses = ["pending", "reviewed", "shortlisted", "rejected"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # Validate score if provided
        if score is not None and (score < 0 or score > 100):
            raise HTTPException(status_code=400, detail="Score must be between 0 and 100")
        
        # Update application
        update_data = {
            "status": status,
            "reviewed_at": datetime.datetime.now(datetime.timezone.utc)
        }
        
        if score is not None:
            update_data["score"] = score
        
        if feedback:
            update_data["feedback"] = feedback
        
        result = applications_collection.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to update application")
        
        return {"message": "Application updated successfully"}
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail="Invalid application ID")

@router.get("/{application_id}")
async def get_application_details(application_id: str):
    """Get detailed information about a specific application"""
    try:
        application = applications_collection.find_one({"_id": ObjectId(application_id)})
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        application["_id"] = str(application["_id"])
        application["applied_at"] = application["applied_at"].isoformat() if application.get("applied_at") else None
        application["reviewed_at"] = application["reviewed_at"].isoformat() if application.get("reviewed_at") else None
        
        # Get additional job details
        job = jobs_collection.find_one({"_id": ObjectId(application["job_id"])})
        if job:
            application["job_details"] = {
                "title": job.get("title", ""),
                "company": job.get("company", ""),
            }
        
        # Get student details
        student = students_collection.find_one({"email": application["student_email"]})
        if student:
            application["student_details"] = {
                "name": student.get("name", ""),
                "email": student.get("email", ""),
                "university": student.get("university", ""),
            }
        
        return application
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail="Invalid application ID")

@router.delete("/{application_id}")
async def withdraw_application(application_id: str, student_email: str):
    """Allow student to withdraw their application"""
    try:
        # Decode URL-encoded email
        decoded_email = unquote(student_email)
        
        # Verify application exists and belongs to the student
        application = applications_collection.find_one({
            "_id": ObjectId(application_id),
            "student_email": decoded_email
        })
        if not application:
            raise HTTPException(status_code=404, detail="Application not found or unauthorized")
        
        # Only allow withdrawal if application is still pending
        if application.get("status") != "pending":
            raise HTTPException(status_code=400, detail="Cannot withdraw application that has been reviewed")
        
        result = applications_collection.delete_one({"_id": ObjectId(application_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Failed to withdraw application")
        
        return {"message": "Application withdrawn successfully"}
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail="Invalid application ID")
    
from .jobs import evaluate_llm_feedback_for_all
    
@router.post("/trigger-evaluation")
async def trigger_evaluation():
    results = await evaluate_llm_feedback_for_all()
    return {"message": f"{results['evaluated']} applications evaluated", "results": results["results"]}
