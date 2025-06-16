import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { recruiterAPI, jobAPI, applicationAPI } from "../services/api.js";
import toast from "react-hot-toast";
import LoadingSpinner from "./LoadingSpinner.jsx";
import { createPortal } from 'react-dom';


export default function RecruiterDashboard() {
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [recruiterEmail, setRecruiterEmail] = useState(location.state?.email || "");
  
  // State for different sections
  const [profile, setProfile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  
  // Job creation state/edited
  const [jobForm, setJobForm] = useState({
    title: "",
    company: "",
    location: "",
    job_type: "full-time",
    salary_range: "",
    description: "",
    job_description_file: null, // Added PDF file state
    creating: false
  });

  // PDF upload state
  const [pdfUploading, setPdfUploading] = useState(false);
  const [pdfPreview, setPdfPreview] = useState(null);

  // Application management state
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [feedbackForm, setFeedbackForm] = useState({
    status: "",
    feedback: "",
    submitting: false
  });

  useEffect(() => {
    if (!recruiterEmail) {
      const email = prompt("Please enter your email to access dashboard:");
      if (email) {
        setRecruiterEmail(email);
      } else {
        navigate("/");
        return;
      }
    }
    loadDashboardData();
  }, [recruiterEmail]);

  const loadDashboardData = async () => {
    if (!recruiterEmail) return;
    
    setLoading(true);
    try {
      const [profileData, jobsData, applicationsData, analyticsData] = await Promise.all([
        recruiterAPI.getProfile(recruiterEmail),
        recruiterAPI.getJobs(recruiterEmail),
        recruiterAPI.getApplications(recruiterEmail),
        recruiterAPI.getAnalytics(recruiterEmail)
      ]);

      setProfile(profileData);
      setJobs(jobsData.jobs || []);
      setApplications(applicationsData.applications || []);
      setAnalytics(analyticsData);
    } catch (error) {
      toast.error("Failed to load dashboard data");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };
  const [evaluating, setEvaluating] = useState(false);

  const handleEvaluateAll = async () => {
  try {
    setEvaluating(true);
    const res = await applicationAPI.evaluateAll();
    await loadDashboardData()
    alert(res.message);  // or toast if preferred
  } catch (err) {
    console.error(err);
    alert("Error evaluating applications");
  } finally {
    setEvaluating(false);
  }
};

  const handleJobFormChange = (e) => {
    const { name, value } = e.target;
    setJobForm({
      ...jobForm,
      [name]: value
    });
  };

  // Handle PDF file selection
  const handlePdfFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      if (file.type !== 'application/pdf') {
        toast.error("Please select a PDF file");
        return;
      }
      
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        toast.error("PDF file size should be less than 10MB");
        return;
      }

      setJobForm({
        ...jobForm,
        job_description_file: file
      });

      // Create preview URL
      setPdfPreview({
        name: file.name,
        size: (file.size / 1024 / 1024).toFixed(2) + ' MB'
      });
    }
  };

  // Remove PDF file
  const removePdfFile = () => {
    setJobForm({
      ...jobForm,
      job_description_file: null
    });
    setPdfPreview(null);
    // Clear file input
    const fileInput = document.getElementById('job_description_file');
    if (fileInput) fileInput.value = '';
  };

  const handleCreateJob = async (e) => {
    e.preventDefault();
    setJobForm({ ...jobForm, creating: true });
    
    try {
      // Create FormData for file upload
      const formData = new FormData();
      
      // Add all job data to FormData
      formData.append('title', jobForm.title);
      formData.append('company', jobForm.company);
      formData.append('location', jobForm.location);
      formData.append('job_type', jobForm.job_type);
      formData.append('description', jobForm.description);
      formData.append('recruiter_email', recruiterEmail);
      
      
      // Add PDF file if selected
      if (jobForm.job_description_file) {
        formData.append('job_description_file', jobForm.job_description_file);
      }

      await jobAPI.createWithFile(formData);
      toast.success("Job posted successfully!");
      
      // Reset form
      setJobForm({
        title: "",
        company: "",
        location: "",
        job_type: "full-time",
        description: "",
        job_description_file: null,
        creating: false
      });
      setPdfPreview(null);
      
      // Clear file input
      const fileInput = document.getElementById('job_description_file');
      if (fileInput) fileInput.value = '';
      
      // Reload jobs
      const jobsData = await recruiterAPI.getJobs(recruiterEmail);
      setJobs(jobsData.jobs || []);
    } catch (error) {
      toast.error(error.message || "Failed to create job");
      setJobForm({ ...jobForm, creating: false });
    }
  };

  const handleDeleteJob = async (jobId) => {
    if (!confirm("Are you sure you want to delete this job posting?")) return;
    
    try {
      await jobAPI.delete(jobId);
      toast.success("Job deleted successfully!");
      setJobs(jobs.filter(job => job._id !== jobId));
    } catch (error) {
      toast.error("Failed to delete job");
    }
  };

  const handleApplicationAction = async (applicationId, status, feedback = "") => {
    setFeedbackForm({ ...feedbackForm, submitting: true });
    try {
      await applicationAPI.updateStatus(applicationId, {
        status,
        feedback,
        recruiter_email: recruiterEmail
      });
      toast.success(`Application ${status} successfully!`);
      
      // Update applications list
      setApplications(applications.map(app =>
        app._id === applicationId
          ? { ...app, status, feedback }
         : app
      ));
      setSelectedApplication(null);
      setFeedbackForm({ status: "", feedback: "", submitting: false });
    } catch (error) {
      toast.error("Failed to update application");
      setFeedbackForm({ ...feedbackForm, submitting: false });
    }
  };

  const fetchLLMFeedback = async () => {
    try {
      const res = await jobAPI.evaluateAllApplications();
      console.log("✅ LLM Feedback processed:", res);
    } catch (err) {
      console.error("❌ Failed to get LLM feedback:", err);
      toast.error("Failed to evaluate applications");
    }
  };
  const [hasEvaluated, setHasEvaluated] = useState(false);

// Reset evaluation flag if user switches away
useEffect(() => {
  if (activeTab !== "applications") {
    setHasEvaluated(false);
  }
}, [activeTab]);

// Only trigger once per entry into "applications"
useEffect(() => {
  if (activeTab === "applications" && !hasEvaluated) {
    fetchLLMFeedback().then(() => {
      setHasEvaluated(true);
    });
  }
}, [activeTab, hasEvaluated]);


  const getStatusColor = (status) => {
    switch (status) {
      case "pending": return "bg-yellow-100 text-yellow-800";
      case "reviewed": return "bg-blue-100 text-blue-800";
      case "shortlisted": return "bg-green-100 text-green-800";
      case "rejected": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getJobTypeColor = (type) => {
    switch (type) {
      case "full-time": return "bg-green-100 text-green-800";
      case "part-time": return "bg-blue-100 text-blue-800";
      case "contract": return "bg-purple-100 text-purple-800";
      case "internship": return "bg-orange-100 text-orange-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="xl" />
      </div>
    );
  }

  



  return (
    <div>
      {loading ? (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="xl" />
      </div>
) : (
    <>
    <div className="min-h-screen bg-gray-50 relative z-0">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Recruiter Dashboard</h1>
              <p className="text-gray-600">Welcome back, {profile?.name || "Recruiter"}!</p>
            </div>
            <button
              onClick={() => navigate("/")}
              className="bg-blue-100 text-black px-4 py-2 rounded-md hover:bg-gray-700"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: "dashboard", name: "Dashboard" },
              { id: "jobs", name: "My Jobs" },
              { id: "create-job", name: "Post New Job" },
              { id: "applications", name: "Applications" },
              { id: "profile", name: "Profile" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? "border-indigo-500 text-indigo-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Dashboard Overview */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            {/* Analytics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900">Active Jobs</h3>
                <p className="text-3xl font-bold text-indigo-600">{jobs.length}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900">Total Applications</h3>
                <p className="text-3xl font-bold text-green-600">{analytics?.total_applications || 0}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900">Shortlisted</h3>
                <p className="text-3xl font-bold text-blue-600">{analytics?.shortlisted || 0}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900">Pending Review</h3>
                <p className="text-3xl font-bold text-yellow-600">{analytics?.pending || 0}</p>
              </div>
            </div>

            {/* Recent Applications */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Recent Applications</h3>
              </div>
              <div className="p-6">
                {applications.slice(0, 5).map((app) => (
                  <div key={app._id} className="flex justify-between items-center py-3 border-b border-gray-100 last:border-b-0">
                    <div>
                      <h4 className="font-medium text-gray-900">{app.student_name}</h4>
                      <p className="text-sm text-gray-600">{app.job_title}</p>
                      <p className="text-xs text-gray-500">Applied: {new Date(app.applied_at).toLocaleDateString()}</p>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(app.status)}`}>
                        {app.status}
                      </span>
                      {app.score && (
                        <p className="text-sm text-gray-600 mt-1">Score: {app.score}%</p>
                      )}
                    </div>
                  </div>
                ))}
                {applications.length === 0 && (
                  <p className="text-gray-500 text-center py-4">No applications yet</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* My Jobs */}
        {activeTab === "jobs" && (
          <div className="space-y-4">
            {jobs.map((job) => (
              <div key={job._id} className="bg-white p-6 rounded-lg shadow">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-gray-900">{job.title}</h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getJobTypeColor(job.job_type)}`}>
                        {job.job_type}
                      </span>
                    </div>
                    <p className="text-gray-600">{job.company}</p>
                    <p className="text-sm text-gray-500 mt-1">{job.location}</p>
                    <p className="text-gray-700 mt-3">{job.description}</p>
                    
                    
                    {/* Job Description PDF Link */}
                    {job.job_description_file_url && (
                      <div className="mt-3">
                        <a
                          href={job.job_description_file_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center text-sm text-indigo-600 hover:text-indigo-800"
                        >
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          View Job Description PDF
                        </a>
                      </div>
                    )}
                    
                    <div className="mt-3 text-sm text-gray-600">
                      <p>Posted: {new Date(job.created_at).toLocaleDateString()}</p>
                      <p>Applications: {job.application_count || 0}</p>
                    </div>
                  </div>
                  
                  <div className="ml-4 flex flex-col space-y-2">
                    <button
                      onClick={() => {
                        setActiveTab("applications");
                        // Filter applications for this job
                      }}
                      className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
                    >
                      View Applications
                    </button>
                    <button
                      onClick={() => handleDeleteJob(job._id)}
                      className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 text-sm"
                    >
                      Delete Job
                    </button>
                  </div>
                </div>
              </div>
            ))}
            {jobs.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500">No jobs posted yet.</p>
                <button
                  onClick={() => setActiveTab("create-job")}
                  className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                >
                  Post Your First Job
                </button>
              </div>
            )}
          </div>
        )}

        {/* Create Job */}
        {activeTab === "create-job" && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Post New Job</h3>
            </div>
            <div className="p-6">
              <form onSubmit={handleCreateJob} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Title *
                    </label>
                    <input
                      type="text"
                      name="title"
                      required
                      value={jobForm.title}
                      onChange={handleJobFormChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="e.g.,Software Engineer"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Company Name *
                    </label>
                    <input
                      type="text"
                      name="company"
                      required
                      value={jobForm.company}
                      onChange={handleJobFormChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Company name"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Location *
                    </label>
                    <input
                      type="text"
                      name="location"
                      required
                      value={jobForm.location}
                      onChange={handleJobFormChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="e.g., New York, NY or Remote"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Type *
                    </label>
                    <select
                      name="job_type"
                      value={jobForm.job_type}
                      onChange={handleJobFormChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="full-time">Full-time</option>
                      <option value="part-time">Part-time</option>
                      <option value="contract">Contract</option>
                      <option value="internship">Internship</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Job Description *
                  </label>
                  <textarea
                    name="description"
                    required
                    rows={4}
                    value={jobForm.description}
                    onChange={handleJobFormChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Describe the role, responsibilities, and what you're looking for..."
                  />
                </div>

                {/* PDF Upload Section */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Job Description PDF (Mandatory)
                  </label>
                  <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                    <div className="space-y-1 text-center">
                      {pdfPreview ? (
                        <div className="flex items-center justify-center space-x-4">
                          <div className="flex items-center space-x-2">
                            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <div className="text-left">
                              <p className="text-sm font-medium text-gray-900">{pdfPreview.name}</p>
                              <p className="text-xs text-gray-500">{pdfPreview.size}</p>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={removePdfFile}
                            className="text-red-600 hover:text-red-800"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      ) : (
                        <>
                          <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          <div className="flex text-sm text-gray-600">
                            <label htmlFor="job_description_file" className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                              <span>Upload a PDF file</span>
                              <input
                                id="job_description_file"
                                name="job_description_file"
                                type="file"
                                accept=".pdf"
                                onChange={handlePdfFileChange}
                                className="sr-only"
                              />
                            </label>
                            <p className="pl-1">or drag and drop</p>
                          </div>
                          <p className="text-xs text-gray-500">PDF up to 10MB</p>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                
                <button
                  type="submit"
                  disabled={jobForm.creating}
                  className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {jobForm.creating ? <LoadingSpinner size="sm" /> : "Post Job"}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Applications */}
        {activeTab === "applications" && (
          <div className="space-y-6">
            {/* Application Filters */}
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-800">Applications</h2>
              <button
                onClick={handleEvaluateAll}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={evaluating}
              >
                {evaluating ? "Evaluating..." : "Evaluate All"}
              </button>
              </div>
              <div className="flex flex-wrap gap-4">
                <select className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
                  <option value="">All Jobs</option>
                  {jobs.map(job => (
                    <option key={job._id} value={job._id}>{job.title}</option>
                  ))}
                </select>
                <select className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
                  <option value="">All Status</option>
                  <option value="pending">Pending</option>
                  <option value="reviewed">Reviewed</option>
                  <option value="shortlisted">Shortlisted</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
            </div>

            {/* Applications List */}
            <div className="space-y-4">
              {applications.map((app) => (
                <div key={app._id} className="bg-white p-6 rounded-lg shadow">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">{app.student_name}</h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(app.status)}`}>
                          {app.status}
                        </span>
                      </div>
                      <p className="text-gray-600">{app.job_title}</p>
                      <p className="text-sm text-gray-500">Applied: {new Date(app.applied_at).toLocaleDateString()}</p>
                      
                      {app.score && (
                        <div className="mt-2">
                          <p className="text-sm font-medium text-gray-900">CV Match Score: {app.score}%</p>
                          <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                            <div 
                              className="bg-indigo-600 h-2 rounded-full" 
                              style={{ width: `${app.score}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                      
                      {app.feedback && (
                        <div className="mt-3">
                          <p className="text-sm font-medium text-gray-900">Feedback:</p>
                          <p className="text-sm text-gray-700 mt-1">{app.feedback}</p>
                        </div>
                      )}

                      {app.strengths && (
                        <div className="mt-3">
                          <p className="text-sm font-medium text-gray-900">Strengths:</p>
                          <p className="text-sm text-gray-700 mt-1">{app.strengths}</p>
                        </div>
                      )}

                      {app.weaknesses && (
                        <div className="mt-3">
                          <p className="text-sm font-medium text-gray-900">Weaknesses:</p>
                          <p className="text-sm text-gray-700 mt-1">{app.weaknesses}</p>
                        </div>
                      )}
                    </div>
                    
                    <div className="ml-4 flex flex-col space-y-2">
                      {app.cv_url && (
                        <a
                          href={app.cv_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm text-center"
                        >
                          View CV
                        </a>
                      )}
                      <button
                        onClick={() => setSelectedApplication(app)}
                        className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 text-sm"
                      >
                        Update Status
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              {applications.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-gray-500">No applications received yet</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Profile */}
        {activeTab === "profile" && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Profile Information</h3>
            </div>
            <div className="p-6">
              {profile ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Name</label>
                      <p className="mt-1 text-sm text-gray-900">{profile.name}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Email</label>
                      <p className="mt-1 text-sm text-gray-900">{profile.email}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Company</label>
                      <p className="mt-1 text-sm text-gray-900">{profile.company}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Position</label>
                      <p className="mt-1 text-sm text-gray-900">{profile.position || "Not provided"}</p>
                    </div>
                  </div>
                  
                  <div className="pt-4">
                    <button
                      onClick={() => {
                        toast.info("Profile editing feature coming soon!");
                      }}
                      className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                    >
                      Edit Profile
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500">Profile information not available</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Application Status Update Modal */}
    </div>

  {selectedApplication && (
  <div
    style={{
      position: "fixed",
      top: 0,
      left: 0,
      width: "100vw",
      height: "100vh",
      backgroundColor: "rgba(0,0,0,0.5)",
      zIndex: 9999,
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
    }}
  >
    <div
      style={{
        background: "white",
        borderRadius: "0.5rem",
        padding: "1.5rem",
        width: "100%",
        maxWidth: "28rem", // Tailwind's max-w-md
        boxShadow: "0 10px 25px rgba(0,0,0,0.1)",
      }}
    >
      <div style={{ marginTop: "0.75rem" }}>
        <h3
          style={{
            fontSize: "1.125rem",
            fontWeight: 500,
            color: "#1f2937", // gray-900
            marginBottom: "1rem",
          }}
        >
          Update Application Status
        </h3>

        <p
          style={{
            fontSize: "0.875rem",
            color: "#4b5563", // gray-600
            marginBottom: "1rem",
          }}
        >
          Application from{" "}
          <strong>{selectedApplication.student_name}</strong> for{" "}
          <strong>{selectedApplication.job_title}</strong>
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.875rem",
                fontWeight: 500,
                marginBottom: "0.5rem",
                color: "#374151", // gray-700
              }}
            >
              Status
            </label>
            <select
              value={feedbackForm.status}
              onChange={(e) =>
                setFeedbackForm({ ...feedbackForm, status: e.target.value })
              }
              style={{
                width: "100%",
                padding: "0.5rem 0.75rem",
                border: "1px solid #d1d5db", // gray-300
                borderRadius: "0.375rem",
                outline: "none",
                fontSize: "0.875rem",
              }}
            >
              <option value="">Select status</option>
              <option value="reviewed">Reviewed</option>
              <option value="shortlisted">Shortlisted</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.875rem",
                fontWeight: 500,
                marginBottom: "0.5rem",
                color: "#374151",
              }}
            >
              Feedback (optional)
            </label>
            <textarea
              rows={3}
              value={feedbackForm.feedback}
              onChange={(e) =>
                setFeedbackForm({ ...feedbackForm, feedback: e.target.value })
              }
              placeholder="Provide feedback to the candidate..."
              style={{
                width: "100%",
                padding: "0.5rem 0.75rem",
                border: "1px solid #d1d5db",
                borderRadius: "0.375rem",
                fontSize: "0.875rem",
                outline: "none",
              }}
            />
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: "0.75rem",
            marginTop: "1.5rem",
          }}
        >
          <button
            onClick={() => {
              setSelectedApplication(null)
              setFeedbackForm({ status: "", feedback: "", submitting: false });
            }}
            style={{
              backgroundColor: "#d1d5db", // gray-300
              color: "#374151", // gray-700
              padding: "0.5rem 1rem",
              borderRadius: "0.375rem",
              cursor: "pointer",
            }}
          >
            Cancel
          </button>

          <button
            onClick={() =>
              handleApplicationAction(
                selectedApplication._id,
                feedbackForm.status,
                feedbackForm.feedback
              )
            }
            disabled={!feedbackForm.status || feedbackForm.submitting}
            style={{
              backgroundColor: "#4f46e5", // indigo-600
              color: "#fff",
              padding: "0.5rem 1rem",
              borderRadius: "0.375rem",
              cursor: feedbackForm.status ? "pointer" : "not-allowed",
              opacity: feedbackForm.status ? 1 : 0.5,
              display: "flex",
              alignItems: "center",
            }}
          >
            {feedbackForm.submitting ? (
              <>
                <LoadingSpinner size="sm" />
                <span style={{ marginLeft: "0.5rem" }}>Updating...</span>
              </>
            ) : (
              "Update Status"
            )}
          </button>
        </div>
      </div>
    </div>
  </div>
)}

    
    </>
    )}
    </div>
  );
}
                       
