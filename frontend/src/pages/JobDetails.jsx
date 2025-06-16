import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { jobAPI } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";

export default function JobDetails() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadJobDetails();
  }, [jobId]);

  const loadJobDetails = async () => {
    try {
      const jobData = await jobAPI.getById(jobId);
      setJob(jobData);
    } catch (error) {
      console.error("Failed to load job details:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="xl" />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Job Not Found</h2>
          <button
            onClick={() => navigate("/")}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">{job.title}</h1>
          <p className="text-xl text-gray-600 mb-6">{job.company}</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Location</h3>
              <p className="text-gray-600">{job.location}</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Job Type</h3>
              <p className="text-gray-600">{job.job_type}</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Experience Level</h3>
              <p className="text-gray-600">{job.experience_level}</p>
            </div>
            {job.salary_range && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Salary Range</h3>
                <p className="text-gray-600">{job.salary_range}</p>
              </div>
            )}
          </div>

          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Description</h3>
            <p className="text-gray-700 whitespace-pre-line">{job.description}</p>
          </div>

          {job.requirements && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Requirements</h3>
              <p className="text-gray-700 whitespace-pre-line">{job.requirements}</p>
            </div>
          )}

          {job.required_skills && job.required_skills.length > 0 && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Required Skills</h3>
              <div className="flex flex-wrap gap-2">
                {job.required_skills.map((skill, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-indigo-100 text-indigo-800 text-sm rounded-full"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex space-x-4">
            <button
              onClick={() => navigate(-1)}
              className="bg-gray-600 text-white px-6 py-2 rounded-md hover:bg-gray-700"
            >
              Back
            </button>
            <button
              onClick={() => {
                // Navigate to application or login
                navigate("/student/dashboard");
              }}
              className="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700"
            >
              Apply Now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
