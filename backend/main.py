#backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.students import router as students_router
from routes.recruiters import router as recruiters_router
from routes.jobs import router as jobs_router
from routes.applications import router as applications_router
import uvicorn

app = FastAPI(
    title="CV Evaluator API",
    description="Backend API for CV evaluation and job matching system",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(students_router, prefix="/api/students", tags=["Students"])
app.include_router(recruiters_router, prefix="/api/recruiters", tags=["Recruiters"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(applications_router, prefix="/api/applications", tags=["Applications"])

@app.get("/")
async def root():
    return {"message": "CV Evaluator API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
