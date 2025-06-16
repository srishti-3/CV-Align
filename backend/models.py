from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    RECRUITER = "recruiter"

class StudentRegistration(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    skills: List[str] = []

class StudentProfile(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    cv_count: int = 0

class RecruiterRegistration(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    company: str = Field(..., min_length=2, max_length=200)

class JobPosting(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    company: str = Field(..., min_length=2, max_length=200)
    description: str
    location: Optional[str] = ""
    job_type: Optional[str] = "Full-time"
    recruiter_email: EmailStr
    job_description_pdf_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class CVUpload(BaseModel):
    student_email: EmailStr
    cv_name: str = Field(..., min_length=1, max_length=100)
    cv_url: str

class JobApplication(BaseModel):
    student_email: EmailStr
    recruiter_email: EmailStr
    job_id: str
    cv_id: str
    cv_url: str
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # pending, reviewed, shortlisted, rejected
    score: Optional[float] = None
    feedback: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None

class ParsedCV(BaseModel):
    name: str
    student_email: EmailStr
    phones: Optional[List[str]] = []
    branch: Optional[str]
    cgpa: Optional[float]
    education: Optional[List[str]] = []
    projects: Optional[List[str]] = []
    achievements: Optional[List[str]] = []
    skills: Optional[Dict[str, List[str]]] = {}
    extracted_skills: Optional[List[str]] = []
    courses: Optional[List[str]] = []
    extracurriculars: Optional[List[str]] = []
    positions: Optional[List[str]] = []

class ParsedJD(BaseModel):
    job_id: str
    recruiter_email: EmailStr
    title: str
    company: str
    parsed_data: Dict
    structured: Dict
