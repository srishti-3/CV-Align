// App.jsx
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import Home from "./pages/Home";
import StudentDashboard from "./components/StudentDashboard";
import RecruiterDashboard from "./components/RecruiterDashboard";
import StudentRegistration from "./pages/StudentRegistration";
import RecruiterRegistration from "./pages/RecruiterRegistration";
import Header from "./pages/Header";
import Footer from "./pages/Footer";
import JobDetails from "./pages/JobDetails";
import ApplicationDetails from "./pages/ApplicationDetails";
import "./App.css";

function App() {
  return (
    <Router>
      <div className="app-container">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/student/register" element={<StudentRegistration />} />
            <Route path="/student/dashboard" element={<StudentDashboard />} />
            <Route path="/recruiter/register" element={<RecruiterRegistration />} />
            <Route path="/recruiter/dashboard" element={<RecruiterDashboard />} />
            <Route path="/job/:jobId" element={<JobDetails />} />
            <Route path="/application/:applicationId" element={<ApplicationDetails />} />
          </Routes>
        </main>
        <Footer />
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App;
