#backend/routes/jobs.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from models import JobPosting
from database import jobs_collection, recruiters_collection, applications_collection, parsed_jd_collection, parsed_cv_collection
from utils.cloudinary_upload import upload_job_description
from bson import ObjectId
from typing import List, Optional
import datetime
from .parse_jd import parse_jd_pdf,  extract_structured_values
from .students import parse_all_uploaded_cvs
from .score import evaluate_cv
import requests
import tempfile
from .train_model import model
from dotenv import load_dotenv
import os

load_dotenv()
gemini = os.getenv("GEMINI")

# Suppress oneDNN logs and general TF warnings
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import warnings
warnings.filterwarnings("ignore") 

from sentence_transformers import SentenceTransformer
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")

router = APIRouter()

from urllib.parse import unquote

@router.post("/create")
async def create_job(
    title: str = Form(...),
    company: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    job_type: str = Form("Full-time"),
    recruiter_email: str = Form(...),
    job_description_file: UploadFile = File(...)
):
    """Create a new job posting"""
    try:
        # Fixed: Decode URL-encoded email
        decoded_email = unquote(recruiter_email.strip())
        
        # Verify recruiter exists
        recruiter = recruiters_collection.find_one({"email": decoded_email})
        if not recruiter:
            raise HTTPException(status_code=404, detail="Recruiter not found")
        
        # Validate required fields
        if not title or not title.strip():
            raise HTTPException(status_code=422, detail="Job title is required")
        
        if not company or not company.strip():
            raise HTTPException(status_code=422, detail="Company name is required")
        
        if not recruiter_email or not recruiter_email.strip():
            raise HTTPException(status_code=422, detail="Recruiter email is required")
        
        # Validate file upload - MANDATORY
        if not job_description_file or not job_description_file.filename:
            raise HTTPException(status_code=422, detail="Job description PDF file is required")
        
        if not job_description_file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=422, detail="Job description must be a PDF file")
        
        # Fixed: Add file size validation
        if hasattr(job_description_file, 'size') and job_description_file.size and job_description_file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=422, detail="File size must be less than 10MB")
        
        # Upload job description file
        try:
            job_description_pdf_url = upload_job_description(job_description_file)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to upload job description: {str(e)}")
        
        # Fixed: Validate job_type against allowed values
        valid_job_types = ["Full-time", "Part-time", "Contract", "Internship", "Remote"]
        validated_job_type = job_type.strip() if job_type and job_type.strip() in valid_job_types else "Full-time"
        
        job_data = {
            "title": title.strip(),
            "company": company.strip(),
            "description": description.strip() if description else "",
            "location": location.strip() if location else "",
            "job_type": validated_job_type,
            "recruiter_email": decoded_email,  # Fixed: Use decoded email
            "job_description_pdf_url": job_description_pdf_url,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "is_active": True,
            "application_count": 0  # Fixed: Initialize application count
        }
        
        result = jobs_collection.insert_one(job_data)
        
        # Update recruiter's job count
        recruiters_collection.update_one(
            {"email": decoded_email},  # Fixed: Use decoded email
            {"$inc": {"jobs_posted": 1}}
        )
        
        return {
            "message": "Job created successfully", 
            "job_id": str(result.inserted_id),
            "title": job_data["title"],
            "company": job_data["company"]
        }
    
    except HTTPException:
        # Fixed: Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        # Fixed: Better error handling for unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
#PARSE JD_S APPLIED HERE
parsed_jobs = []

@router.get("/parse-all-jds")
async def parse_all_job_descriptions():
    global parsed_jobs
    jobs = list(jobs_collection.find({"job_description_pdf_url": {"$exists": True}}))
    
    parsed_results = []

    for job in jobs:
        try:
            #if parsed_jd_collection.find_one({"job_id": str(job["job_id"])}):
                #continue  # Skip if already parsed
            
            # Download the JD PDF
            response = requests.get(job["job_description_pdf_url"])
            if response.status_code != 200:
                raise Exception("Failed to download JD")

            # Save PDF to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(response.content)
                file_path = tmp.name

            # Step 1: Parse raw JD text
            parsed_data = parse_jd_pdf(file_path)

            # Step 2: Extract structured fields
            structured = extract_structured_values(parsed_data,model)

            parsed_jd_collection.insert_one({
                "job_id": str(job["_id"]),
                "recruiter_email": job["recruiter_email"],
                "title": job["title"],
                "company": job["company"],
                "parsed_data": parsed_data,
                "structured": structured
            });

            # Collect response
            parsed_results.append({
                "job_id": str(job["_id"]),
                "recruiter_email": job["recruiter_email"],
                "title": job["title"],
                "company": job["company"],
                "parsed_data": parsed_data,
                "structured": structured
            })

        except Exception as e:
            parsed_results.append({
                "job_id": str(job.get("_id")),
                "error": str(e)
            })
    parsed_jobs = parsed_results
    return {"results": parsed_results}
  
@router.get("/list")
async def list_jobs(skip: int = 0, limit: int = 20, active_only: bool = True):
    """List all jobs with pagination"""
    query = {"is_active": True} if active_only else {}
    jobs = list(jobs_collection.find(query).skip(skip).limit(limit).sort("created_at", -1))
    
    for job in jobs:
        job["_id"] = str(job["_id"])
        job["created_at"] = job["created_at"].isoformat() if job.get("created_at") else None
    
    total_jobs = jobs_collection.count_documents(query)
    
    return {
        "jobs": jobs,
        "total": total_jobs,
        "skip": skip,
        "limit": limit
    }

@router.get("/{job_id}")
async def get_job_details(job_id: str):
    """Get detailed information about a specific job"""
    try:
        job = jobs_collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job["_id"] = str(job["_id"])
        job["created_at"] = job["created_at"].isoformat() if job.get("created_at") else None
        
        # Get application count for this job
        application_count = applications_collection.count_documents({"job_id": ObjectId(job_id)})
        job["application_count"] = application_count
        
        return job
    
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid job ID")

@router.get("/recruiter/{recruiter_email}")
async def get_recruiter_jobs(recruiter_email: str):
    """Get all jobs posted by a specific recruiter"""
    jobs = list(jobs_collection.find({"recruiter_email": recruiter_email}).sort("created_at", -1))
    
    for job in jobs:
        job["_id"] = str(job["_id"])
        job["created_at"] = job["created_at"].isoformat() if job.get("created_at") else None
        # Add application count for each job
        job["application_count"] = applications_collection.count_documents({"job_id": str(job["_id"])})
    
    return {"jobs": jobs}

@router.put("/{job_id}/status")
async def update_job_status(job_id: str, is_active: bool, recruiter_email: str):
    """Update job active status (only by the recruiter who posted it)"""
    try:
        # Verify the job belongs to the recruiter
        job = jobs_collection.find_one({"_id": ObjectId(job_id), "recruiter_email": recruiter_email})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or unauthorized")
        
        result = jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"is_active": is_active}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to update job status")
        
        status_text = "activated" if is_active else "deactivated"
        return {"message": f"Job {status_text} successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid job ID")

@router.delete("/{job_id}")
async def delete_job(job_id: str, recruiter_email: str):
    """Delete a job posting (only by the recruiter who posted it)"""
    try:
        # Verify the job belongs to the recruiter
        job = jobs_collection.find_one({"_id": ObjectId(job_id), "recruiter_email": recruiter_email})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or unauthorized")
        
        # Delete the job
        result = jobs_collection.delete_one({"_id": ObjectId(job_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Failed to delete job")
        
        # Update recruiter's job count
        recruiters_collection.update_one(
            {"email": recruiter_email},
            {"$inc": {"jobs_posted": -1}}
        )
        
        return {"message": "Job deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid job ID")

@router.get("/search/")
async def search_jobs(
    query: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """Search jobs with various filters"""
    search_query = {"is_active": True}
    
    if query:
        search_query["$or"] = [
            {"title": {"$regex": query, "$options": "i"}},
            {"company": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}}
        ]
    
    if location:
        search_query["location"] = {"$regex": location, "$options": "i"}
    
    if job_type:
        search_query["job_type"] = job_type
    
    jobs = list(jobs_collection.find(search_query).skip(skip).limit(limit).sort("created_at", -1))
    
    for job in jobs:
        job["_id"] = str(job["_id"])
        job["created_at"] = job["created_at"].isoformat() if job.get("created_at") else None
    
    total_jobs = jobs_collection.count_documents(search_query)
    
    return {
        "jobs": jobs,
        "total": total_jobs,
        "skip": skip,
        "limit": limit
    }

@router.get("/parsed-jds")
async def get_all_parsed_jds(job_id: str = Query(None)):
    query = {"job_id": job_id} if job_id else {}
    jds = list(parsed_jd_collection.find(query, {"_id": 0}))
    return {"total": len(jds), "data": jds}


@router.post("/evaluate-applications-by-cv/{cv_id}")
async def evaluate_applications(cv_id: str):
    applications = list(applications_collection.find({"cv_id": str(cv_id)}))
    evaluated_results = []

    for app in applications:
        job_id = app.get("job_id")
        student_email = app.get("student_email")

        if not job_id or not student_email:
            continue

        # Make sure both parsed CV and parsed JD exist
        await parse_all_job_descriptions()
        await parse_all_uploaded_cvs()

        parsed_cv_cur = parsed_cv_collection.find_one({"cv_id": ObjectId(cv_id)})
        parsed_jd = parsed_jd_collection.find_one({"job_id": job_id})
        #print(parsed_cv,parsed_jd)
        if not parsed_cv_cur or not parsed_jd:
            continue  # skip if either is missing

        try:
            result = evaluate_cv(
                jd_structured=parsed_jd["structured"],
                jd_sections=parsed_jd["parsed_data"],
                parsed_resume=parsed_cv_cur["parsed"],
                skill2vec_model=model,
                sbert_model=sbert_model
            )

            applications_collection.update_one(
                {"_id": app["_id"]},
                {
                    "$set": {
                        "score": result["final_score"],
                        "feedback": result["eligibility_reason"],
                        "status": "evaluated"
                    }
                }
            )

            evaluated_results.append({
                "course_score": result["course_score"],
                "final_score": result["final_score"],
                "skill_score": result["skill_score"]["final_score"],
                "semantic_score": result["semantic_score"],
            })

        except Exception as e:
            evaluated_results.append({
                "student_email": student_email,
                "job_id": job_id,
                "error": str(e)
            })

    return evaluated_results[0]
    


from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.4, google_api_key=gemini)

feedback_prompt = PromptTemplate.from_template("""
You are an HR assistant evaluating a candidate's suitability for a job role.

Your task is to:
1. Score the candidate's resume **out of 100**, based only on your analysis strictly from 10-98.
2. Provide specific **strengths** that align with the role.
3. Mention **weaknesses** or areas of mismatch.
4. Give a final recommendation: **Strong / Moderate / Weak fit**, with a short justification.

The system may internally estimate some match, but you must ignore those and give your own independent judgment.

Job Description:
{jd_text}

Resume Overview:
{cv_text}

Top Matching Resume Chunks:
{cv_chunks}

Respond in the following format:

<<Score:>>
(Must be a plain integer between 10 and 98 only. Do NOT return decimal or percentage.)

<<Strengths:>>
- ...

<<Weaknesses:>>
- ...

<<Final Recommendation:>>
<Strong / Moderate / Weak fit> — <your short justification>
""")


#feedback_chain = LLMChain(llm=llm, prompt=feedback_prompt)
from langchain_core.runnables import RunnableSequence
feedback_chain = feedback_prompt | llm

from .LLM import chunk_resume, embed_and_upsert_chunks, query_pinecone
from langchain_core.runnables import Runnable  # or use your actual feedback_chain import


async def process_and_evaluate_cv(
    resume_id: str,
    parsed_resume: dict,
    parsed_data: dict,
    structured: dict,
    feedback_chain: Runnable
):
    # Step 1: Chunk and upsert resume
    resume_chunks = chunk_resume(parsed_resume)
    embed_and_upsert_chunks(resume_id=resume_id, chunks=resume_chunks)

    # Step 2: Build query from parsed_data and structured
    jd_query_parts = [
        parsed_data.get("job_role", ""),
        " ".join(parsed_data.get("required_skills", [])),
        " ".join(parsed_data.get("responsibilities", [])),
        " ".join(parsed_data.get("preferred_skills", [])),
        " ".join(structured.get("branches", [])),
        " ".join(structured.get("technologies", [])),
        " ".join(structured.get("non_tech_skills", [])),
        structured.get("domain", "")
    ]
    jd_query = " ".join([part for part in jd_query_parts if part])

    # Step 3: Query Pinecone for top-matching resume chunks
    cv_chunks = query_pinecone(jd_query)
    

    input_data = {
        "jd_text": jd_query,
        "cv_text": "\n".join(resume_chunks),               # make sure it's string
        "cv_chunks": "\n".join(cv_chunks)        # make sure it's string
    }

    # Step 5: Generate feedback
    feedback = await feedback_chain.ainvoke(input_data)

    # Step 6: Print feedback
    #print("FEEDBACK:\n")
    #print(feedback["text"])

    return feedback.content



import re

def parse_llm_feedback(text: str):
    def extract_between(text, start_kw, end_kw):
        start = text.find(start_kw)
        if start == -1:
            return None
        start += len(start_kw)
        end = text.find(end_kw, start) if end_kw else len(text)
        return text[start:end].strip()

    score_text = extract_between(text, "Score:", "Strengths:")
    strengths_text = extract_between(text, "Strengths:", "Weaknesses:")
    weaknesses_text = extract_between(text, "Weaknesses:", "Final Recommendation:")
    recommendation_text = extract_between(text, "Final Recommendation:", None)

    try:
        match = re.search(r"\b([1-9][0-9])\b", score_text)  # match integers from 10–99
        score = int(match.group(1)) if match else 0
        print(score)
        return {
            "score": score,
            "strengths": [
                line.strip("- ").strip()
                for line in strengths_text.splitlines()
                if line.strip().startswith("-")
            ],
            "weaknesses": [
                line.strip("- ").strip()
                for line in weaknesses_text.splitlines()
                if line.strip().startswith("-")
            ],
            "recommendation": recommendation_text.strip()
        }
    except Exception as e:
        print("⚠️ Failed to parse:", e)
        return None




@router.post("/evaluate-llm-feedback")
async def evaluate_llm_feedback_for_all():
    await parse_all_job_descriptions()
    await parse_all_uploaded_cvs()

    applications = list(applications_collection.find({
        "$or": [{"score": {"$exists": False}}, {"score": None}]
    }))
    evaluated_results = []

    for app in applications:
        job_id = app.get("job_id")
        student_email = app.get("student_email")

        if not job_id or not student_email:
            continue
        
        parsed_cv_cur = parsed_cv_collection.find_one({"student_email": student_email})
        parsed_jd = parsed_jd_collection.find_one({"job_id": job_id})

        if not parsed_cv_cur or not parsed_jd:
            continue  # Skip if either is missing

        # Prepare inputs
        resume_id = str(parsed_cv_cur["cv_id"])
        parsed_resume = parsed_cv_cur["parsed"]

        parsed_data = parsed_jd["parsed_data"]
        structured = parsed_jd.get("structured", {})

        # Generate feedback
        try:
            feedback_text = await process_and_evaluate_cv(
                resume_id=resume_id,
                parsed_resume=parsed_resume,
                parsed_data=parsed_data,
                structured=structured,
                feedback_chain=feedback_chain
            )

            parsed_feedback =  parse_llm_feedback(feedback_text) or {}

            # Fetch manual score (already stored by previous pipeline)
            result = await evaluate_applications(resume_id)

            course = result.get("course_score", 0.0)
            skill = result.get("skill_score", 0.0)
            semantic = result.get("semantic_score", 0.0)
            extra = result.get("final_score", 0.0)

            # Scale average to 100
            manual_score = 100 * (course + skill + semantic + extra) / 4



            # Combine scores
            alpha = 0.2  # 40% weight to manual, 60% to LLM
            llm_score = parsed_feedback.get("score", 60)
            
            if(manual_score>=30):
                combined_score = round(alpha * manual_score + (1 - alpha) * llm_score, 2)
            else:
                combined_score = llm_score
            

            if parsed_feedback:
                applications_collection.update_one(
                    {"_id": app["_id"]},
            {
            "$set": {
                "score": combined_score,
                "feedback": parsed_feedback.get("recommendation", ""),
                "strengths": parsed_feedback.get("strengths", []),
                "weaknesses": parsed_feedback.get("weaknesses", [])
            }
            }
            )
                
            else:
                # fallback to raw feedback if parsing fails
                applications_collection.update_one(
                    {"_id": app["_id"]},
                    {"$set": {"feedback": feedback_text}}
                )
            evaluated_results.append({
                "student_email": student_email,
                "job_id": job_id,
                "status": "success"
            })

        except Exception as e:
            evaluated_results.append({
                "student_email": student_email,
                "job_id": job_id,
                "status": "error",
                "error": str(e)
            })

    return {"evaluated": len(evaluated_results), "results": evaluated_results}



