import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { studentAPI, jobAPI, applicationAPI } from "../services/api.js";
import toast from "react-hot-toast";
import LoadingSpinner from "../components/LoadingSpinner";
import './StudentDashboard.css';

export default function StudentDashboard() {
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [studentEmail, setStudentEmail] = useState(location.state?.email || "");
  
  // State for different sections
  const [profile, setProfile] = useState(null);
  const [cvs, setCvs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  
  // CV Upload state
  const [cvUpload, setCvUpload] = useState({
    file: null,
    name: "",
    uploading: false
  });

  // Job search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFilters, setSearchFilters] = useState({
    skills: "",
    location: "",
    job_type: "",
    experience_level: ""
  });

  useEffect(() => {
    if (!studentEmail) {
      const email = prompt("Please enter your email to access dashboard:");
      if (email) {
        setStudentEmail(email);
      } else {
        navigate("/");
        return;
      }
    }
    loadDashboardData();
  }, [studentEmail]);

  const loadDashboardData = async () => {
    if (!studentEmail) return;
    
    setLoading(true);
    try {
      const [profileData, cvsData, applicationsData, jobsData, analyticsData] = await Promise.all([
        studentAPI.getProfile(studentEmail),
        studentAPI.getCVs(studentEmail),
        studentAPI.getApplications(studentEmail),
        jobAPI.getAll(0, 10),
        // studentAPI.getAnalytics(studentEmail)
      ]);

      setProfile(profileData);
      setCvs(cvsData.cvs || []);
      setApplications(applicationsData.applications || []);
      setJobs(jobsData.jobs || []);
      // setAnalytics(analyticsData);
    } catch (error) {
      toast.error("Failed to load dashboard data");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCVUpload = async (e) => {
    e.preventDefault();
    if (!cvUpload.file || !cvUpload.name) {
      toast.error("Please select a file and enter a name");
      return;
    }

    setCvUpload({ ...cvUpload, uploading: true });
    
    try {
      const formData = new FormData();
      formData.append("file", cvUpload.file);
      formData.append("cv_name", cvUpload.name);
      await studentAPI.uploadCV(studentEmail, formData);
      toast.success("CV uploaded successfully!");
      setCvUpload({ file: null, name: "", uploading: false });
      
      // Reload CVs
      const cvsData = await studentAPI.getCVs(studentEmail);
      setCvs(cvsData.cvs || []);
    } catch (error) {
      toast.error(error.message || "CV upload failed");
      setCvUpload({ ...cvUpload, uploading: false });
    }
  };

  const handleDeleteCV = async (cvId) => {
    if (!confirm("Are you sure you want to delete this CV?")) return;
    
    try {
      await studentAPI.deleteCV(studentEmail, cvId);
      toast.success("CV deleted successfully!");
      setCvs(cvs.filter(cv => cv._id !== cvId));
    } catch (error) {
      toast.error("Failed to delete CV");
    }
  };

  const handleJobSearch = async () => {
    try {
      const params = {
        query: searchQuery,
        ...searchFilters,
        skip: 0,
        limit: 20
      };
      
      const result = await jobAPI.search(params);
      setJobs(result.jobs || []);
    } catch (error) {
      toast.error("Search failed");
    }
  };

  const handleApplyJob = async (jobId) => {
    if (cvs.length === 0) {
      toast.error("Please upload a CV first");
      return;
    }
    const selectedCvId = cvs[0]._id; // Use first CV for simplicity
    
    try {
      const formData = new FormData();
      formData.append("student_email", studentEmail);
      formData.append("job_id", jobId);
      formData.append("cv_id", selectedCvId);
      await applicationAPI.apply(formData);
      toast.success("Application submitted successfully!");
      
      // Reload applications
      const applicationsData = await studentAPI.getApplications(studentEmail);
      setApplications(applicationsData.applications || []);
    } catch (error) {
      toast.error(error.message || "Application failed");
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "pending": return "status-pending";
      case "reviewed": return "status-reviewed";
      case "shortlisted": return "status-shortlisted";
      case "rejected": return "status-rejected";
      default: return "status-default";
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <LoadingSpinner size="xl" />
      </div>
    );
  }

  return (
    <div className="student-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-container">
          <div className="header-content">
            <div>
              <h1 className="header-title">Student Dashboard</h1>
              <p className="header-subtitle">Welcome back, {profile?.name || "Student"}!</p>
            </div>
            <button
              onClick={() => navigate("/")}
              className="logout-btn"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="main-container">
        {/* Navigation Tabs */}
        <div className="nav-tabs">
          <nav className="nav-tabs-list">
            {[
              { id: "dashboard", name: "Dashboard" },
              { id: "jobs", name: "Browse Jobs" },
              { id: "applications", name: "My Applications" },
              { id: "cvs", name: "My CVs" },
              { id: "profile", name: "Profile" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`nav-tab ${activeTab === tab.id ? 'nav-tab-active' : ''}`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Dashboard Overview */}
        {activeTab === "dashboard" && (
          <div className="dashboard-content">
            {/* Analytics Cards */}
            <div className="analytics-grid">
              <div className="analytics-card">
                <h3 className="analytics-title">Total Applications</h3>
                <p className="analytics-value analytics-primary">{analytics?.total_applications || 0}</p>
              </div>
              <div className="analytics-card">
                <h3 className="analytics-title">Average Score</h3>
                <p className="analytics-value analytics-success">{analytics?.average_score || 0}%</p>
              </div>
              <div className="analytics-card">
                <h3 className="analytics-title">Success Rate</h3>
                <p className="analytics-value analytics-info">{analytics?.success_rate || 0}%</p>
              </div>
              <div className="analytics-card">
                <h3 className="analytics-title">CVs Uploaded</h3>
                <p className="analytics-value analytics-secondary">{cvs.length}/3</p>
              </div>
            </div>

            {/* Recent Applications */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Recent Applications</h3>
              </div>
              <div className="card-content">
                {applications.slice(0, 5).map((app) => (
                  <div key={app._id} className="recent-app-item">
                    <div>
                      <h4 className="recent-app-title">{app.job_title}</h4>
                      <p className="recent-app-company">{app.company}</p>
                    </div>
                    <div className="recent-app-status">
                      <span className={`status-badge ${getStatusColor(app.status)}`}>
                        {app.status}
                      </span>
                      {app.score && (
                        <p className="recent-app-score">Score: {app.score}%</p>
                      )}
                    </div>
                  </div>
                ))}
                {applications.length === 0 && (
                  <p className="empty-state">No applications yet</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Browse Jobs */}
        {activeTab === "jobs" && (
          <div className="jobs-content">
            {/* Search and Filters */}
            <div className="card">
              <div className="card-content">
                <div className="search-grid">
                  <input
                    type="text"
                    placeholder="Search jobs..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="form-input"
                  />
                  <input
                    type="text"
                    placeholder="Skills (comma-separated)"
                    value={searchFilters.skills}
                    onChange={(e) => setSearchFilters({...searchFilters, skills: e.target.value})}
                    className="form-input"
                  />
                  <input
                    type="text"
                    placeholder="Location"
                    value={searchFilters.location}
                    onChange={(e) => setSearchFilters({...searchFilters, location: e.target.value})}
                    className="form-input"
                  />
                </div>
                <button
                  onClick={handleJobSearch}
                  className="btn btn-primary"
                >
                  Search Jobs
                </button>
              </div>
            </div>

            {/* Job Listings */}
            <div className="jobs-list">
              {jobs.map((job) => (
                <div key={job._id} className="job-card">
                  <div className="job-header">
                    <div className="job-info">
                      <h3 className="job-title">{job.title}</h3>
                      <p className="job-company">{job.company}</p>
                      <p className="job-meta">{job.location} • {job.job_type}</p>
                      <p className="job-description">{job.description}</p>
                      <div className="job-skills">
                        <p className="skills-label">Required Skills:</p>
                        <div className="skills-list">
                          {job.required_skills?.map((skill, index) => (
                            <span key={index} className="skill-tag">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleApplyJob(job._id)}
                      disabled={applications.some(app => app.job_id === job._id)}
                      className={`btn ${applications.some(app => app.job_id === job._id) ? 'btn-disabled' : 'btn-primary'}`}
                    >
                      {applications.some(app => app.job_id === job._id) ? "Applied" : "Apply"}
                    </button>
                  </div>
                </div>
              ))}
              {jobs.length === 0 && (
                <div className="empty-state-container">
                  <p className="empty-state">No jobs found. Try adjusting your search criteria.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* My Applications */}
        {activeTab === "applications" && (
          <div className="applications-list">
            {applications.map((app) => (
              <div key={app._id} className="application-card">
                <div className="application-header">
                  <div>
                    <h3 className="application-title">{app.job_title}</h3>
                    <p className="application-company">{app.company}</p>
                    <p className="application-date">Applied on: {new Date(app.applied_at).toLocaleDateString()}</p>
                    {app.feedback && (
                      <div className="application-feedback">
                        <p className="feedback-label">Feedback:</p>
                        <p className="feedback-text">{app.feedback}</p>
                      </div>
                    )}
                  </div>
                  <div className="application-status">
                    <span className={`status-badge ${getStatusColor(app.status)}`}>
                      {app.status}
                    </span>
                    {app.score && (
                      <p className="application-score">Score: {app.score}%</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {applications.length === 0 && (
              <div className="empty-state-container">
                <p className="empty-state">No applications yet. Start applying to jobs!</p>
              </div>
            )}
          </div>
        )}

        {/* My CVs */}
        {activeTab === "cvs" && (
          <div className="cvs-content">
            {/* CV Upload Form */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Upload New CV</h3>
              </div>
              <div className="card-content">
                               <form onSubmit={handleCVUpload} className="upload-form">
                  <div className="form-section">
                    <label className="form-label">
                      CV Name
                    </label>
                    <input
                      type="text"
                      value={cvUpload.name}
                      onChange={(e) => setCvUpload({ ...cvUpload, name: e.target.value })}
                      placeholder="e.g., Software Engineer CV"
                      className="form-input"
                      required
                    />
                  </div>
                  <div className="form-section">
                    <label className="form-label">
                      CV File (PDF only)
                    </label>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={(e) => setCvUpload({ ...cvUpload, file: e.target.files[0] })}
                      className="file-input"
                      required
                    />
                  </div>
                  <div className="form-actions">
                    <button
                      type="submit"
                      disabled={cvUpload.uploading || cvs.length >= 3}
                      className={`btn ${cvUpload.uploading || cvs.length >= 3 ? 'btn-disabled' : 'btn-primary'}`}
                    >
                      {cvUpload.uploading ? "Uploading..." : "Upload CV"}
                    </button>
                    {cvs.length >= 3 && (
                      <p className="error-message">Maximum 3 CVs allowed. Delete one to upload a new CV.</p>
                    )}
                  </div>
                </form>
              </div>
            </div>

            {/* CV List */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">My CVs ({cvs.length}/3)</h3>
              </div>
              <div className="card-content">
                {cvs.map((cv) => (
                  <div key={cv._id} className="cv-item">
                    <div className="cv-info">
                      <h4 className="cv-name">{cv.cv_name}</h4>
                      <p className="cv-date">
                        Uploaded: {new Date(cv.uploaded_at).toLocaleDateString()}
                      </p>
                      <p className="cv-filename">
                        File: {cv.file_name}
                      </p>
                    </div>
                    <div className="cv-actions">
                      <a
                        href={cv.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-info btn-sm"
                      >
                        View
                      </a>
                      <button
                        onClick={() => handleDeleteCV(cv._id)}
                        className="btn btn-danger btn-sm"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
                {cvs.length === 0 && (
                  <p className="empty-state">No CVs uploaded yet</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Profile */}
        {activeTab === "profile" && (
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Profile Information</h3>
            </div>
            <div className="card-content">
              {profile ? (
                <div className="profile-content">
                  <div className="profile-grid">
                    <div className="profile-field">
                      <label className="profile-label">Name</label>
                      <p className="profile-value">{profile.name}</p>
                    </div>
                    <div className="profile-field">
                      <label className="profile-label">Email</label>
                      <p className="profile-value">{profile.email}</p>
                    </div>
                    <div className="profile-field">
                      <label className="profile-label">Phone</label>
                      <p className="profile-value">{profile.phone || "Not provided"}</p>
                    </div>
                    <div className="profile-field">
                      <label className="profile-label">University</label>
                      <p className="profile-value">{profile.university || "Not provided"}</p>
                    </div>
                    <div className="profile-field">
                      <label className="profile-label">Degree</label>
                      <p className="profile-value">{profile.degree || "Not provided"}</p>
                    </div>
                    <div className="profile-field">
                      <label className="profile-label">Graduation Year</label>
                      <p className="profile-value">{profile.graduation_year || "Not provided"}</p>
                    </div>
                  </div>
                  
                  {profile.skills && profile.skills.length > 0 && (
                    <div className="profile-skills">
                      <label className="profile-label">Skills</label>
                      <div className="skills-list">
                        {profile.skills.map((skill, index) => (
                          <span key={index} className="skill-badge">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {profile.bio && (
                    <div className="profile-bio">
                      <label className="profile-label">Bio</label>
                      <p className="profile-value">{profile.bio}</p>
                    </div>
                  )}
                  
                  <div className="profile-actions">
                    <button
                      onClick={() => {
                        // You can implement profile editing functionality here
                        toast.info("Profile editing feature coming soon!");
                      }}
                      className="btn btn-primary"
                    >
                      Edit Profile
                    </button>
                  </div>
                </div>
              ) : (
                <div className="empty-state-container">
                  <p className="empty-state">Profile information not available</p>
                  <button
                    onClick={() => {
                      toast.info("Profile creation feature coming soon!");
                    }}
                    className="btn btn-primary"
                  >
                    Create Profile
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
