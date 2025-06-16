#backend/utils/cloudinary_upload.py
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def upload_file(file, folder="cv-evaluator", resource_type="raw"):
    """Upload file to Cloudinary"""
    try:
        result = cloudinary.uploader.upload(
            file.file,
            resource_type=resource_type,
            folder=folder,
            use_filename=True,
            unique_filename=True
        )
        return result["secure_url"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

def upload_cv(file):
    """Upload CV file to Cloudinary"""
    return upload_file(file, folder="cv-evaluator/cvs")

def upload_job_description(file):
    """Upload job description PDF to Cloudinary"""
    return upload_file(file, folder="cv-evaluator/job-descriptions")
