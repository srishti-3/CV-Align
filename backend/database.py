#backend/database.py
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()

mongo_uri = os.getenv("MONGO_URL")
if not mongo_uri:
    raise ValueError("MONGO_URI environment variable is not set")

try:
    client = MongoClient(mongo_uri)
    # Test the connection
    client.admin.command('ping')
    db = client["cv-align"]
    print("Successfully connected to MongoDB")
except ConnectionFailure:
    print("Failed to connect to MongoDB")
    raise

# Collections
students_collection = db["students"]
recruiters_collection = db["recruiters"]
jobs_collection = db["jobs"]
applications_collection = db["applications"]
parsed_cv_collection = db["parsed_cv"]
parsed_jd_collection = db["parsed_jd"] 

parsed_cv_collection.create_index([("student_email", 1), ("cv_id", 1)], unique=True)
parsed_jd_collection.create_index("job_id", unique=True)

