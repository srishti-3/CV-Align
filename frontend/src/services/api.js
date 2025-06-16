const API_BASE = "http://localhost:8000/api";

// Helper function for handling responses
const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Network error" }));
    throw new Error(error.detail || "Request failed");
  }
  return response.json();
};

// Student API calls
export const studentAPI = {
  register: async (data) => {
    const response = await fetch(`${API_BASE}/students/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  login: async (data) => {
  const response = await fetch(`${API_BASE}/students/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
    return handleResponse(response);
  },


  getProfile: async (email) => {
    const response = await fetch(`${API_BASE}/students/profile/${email}`);
    return handleResponse(response);
  },

  uploadCV: async (email, formData) => {
    const response = await fetch(`${API_BASE}/students/upload-cv/${email}`, {
      method: "POST",
      body: formData,
    });
    return handleResponse(response);
  },

  getCVs: async (email) => {
    const response = await fetch(`${API_BASE}/students/cvs/${email}`);
    return handleResponse(response);
  },

  deleteCV: async (email, cvId) => {
    const response = await fetch(`${API_BASE}/students/cvs/${email}/${cvId}`, {
      method: "DELETE",
    });
    return handleResponse(response);
  },

  updateProfile: async (email, data) => {
    const response = await fetch(`${API_BASE}/students/profile/${email}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  getApplications: async (email) => {
    const response = await fetch(`${API_BASE}/students/applications/${email}`);
    return handleResponse(response);
  },

  getAnalytics: async (email) => {
    const response = await fetch(`${API_BASE}/applications/analytics/student/${email}`);
    return handleResponse(response);
  },
};

// Recruiter API calls
export const recruiterAPI = {
  register: async (data) => {
    const response = await fetch(`${API_BASE}/recruiters/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  login: async (data) => {
    const response = await fetch(`${API_BASE}/recruiters/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  getProfile: async (email) => {
    const response = await fetch(`${API_BASE}/recruiters/profile/${email}`);
    return handleResponse(response);
  },

  getJobs: async (email) => {
    const response = await fetch(`${API_BASE}/jobs/recruiter/${email}`);
    return handleResponse(response);
  },

  getApplications: async (email) => {
    const response = await fetch(`${API_BASE}/applications/recruiter/${email}`);
    return handleResponse(response);
  },

  getAnalytics: async (email) => {
    const response = await fetch(`${API_BASE}/applications/analytics/recruiter/${email}`);
    return handleResponse(response);
  },
};

// Job API calls
// Job API calls
export const jobAPI = {
  create: async (formData) => {
    const response = await fetch(`${API_BASE}/jobs/create`, {
      method: "POST",
      body: formData,
    });
    return handleResponse(response);
  },
  evaluateAllApplications: async () => {
  const response = await fetch(`${API_BASE}/jobs/evaluate-llm-feedback`, {
    method: "POST",
  });
  if (!response.ok) throw new Error("Evaluation failed");
  return response.json();
},
  
  // Add this new function for file uploads
  createWithFile: async (formData) => {
    const response = await fetch(`${API_BASE}/jobs/create`, {
      method: "POST",
      body: formData, // FormData automatically sets correct headers for file upload
    });
    return handleResponse(response);
  },

  getAll: async (skip = 0, limit = 20, activeOnly = true) => {
    const response = await fetch(
      `${API_BASE}/jobs/list?skip=${skip}&limit=${limit}&active_only=${activeOnly}`
    );
    return handleResponse(response);
  },

  getById: async (jobId) => {
    const response = await fetch(`${API_BASE}/jobs/${jobId}`);
    return handleResponse(response);
  },

  updateStatus: async (jobId, isActive, recruiterEmail) => {
    const formData = new FormData();
    formData.append("is_active", isActive);
    formData.append("recruiter_email", recruiterEmail);
        
    const response = await fetch(`${API_BASE}/jobs/${jobId}/status`, {
      method: "PUT",
      body: formData,
    });
    return handleResponse(response);
  },

  delete: async (jobId, recruiterEmail) => {
    const formData = new FormData();
    formData.append("recruiter_email", recruiterEmail);
        
    const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
      method: "DELETE",
      body: formData,
    });
    return handleResponse(response);
  },

  search: async (params) => {
    const queryString = new URLSearchParams(params).toString();
    const response = await fetch(`${API_BASE}/jobs/search/?${queryString}`);
    return handleResponse(response);
  },
  
};
 
// Application API calls
export const applicationAPI = {
  apply: async (formData) => {
    const response = await fetch(`${API_BASE}/applications/apply`, {
      method: "POST",
      body: formData,
    });
    return handleResponse(response);
  },
  evaluateAll: async () => {
    const response = await fetch(`${API_BASE}/applications/trigger-evaluation`, {
      method: "POST",
    });
    return handleResponse(response);
  },
  getJobApplications: async (jobId, recruiterEmail) => {
    const response = await fetch(
      `${API_BASE}/applications/job/${jobId}?recruiter_email=${recruiterEmail}`
    );
    return handleResponse(response);
  },

  updateStatus: async (applicationId, formData) => {
    const response = await fetch(`${API_BASE}/applications/${applicationId}/status`, {
      method: "PUT",
      body: formData,
    });
    return handleResponse(response);
  },

  getDetails: async (applicationId) => {
    const response = await fetch(`${API_BASE}/applications/${applicationId}`);
    return handleResponse(response);
  },

  withdraw: async (applicationId, studentEmail) => {
    const formData = new FormData();
    formData.append("student_email", studentEmail);
    
    const response = await fetch(`${API_BASE}/applications/${applicationId}`, {
      method: "DELETE",
      body: formData,
    });
    return handleResponse(response);
  },
};
