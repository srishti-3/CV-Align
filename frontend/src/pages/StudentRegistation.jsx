import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { studentAPI } from "../services/api.js";
import toast from "react-hot-toast";
import LoadingSpinner from "../components/LoadingSpinner";
import "./StudentRegistration.css";

export default function StudentRegistration() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [isLogin, setIsLogin] = useState(true); // toggle form state
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    university: "",
    graduation_year: "",
    password:"",
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);

  try {
    if (isLogin) {
      await studentAPI.login({
        email: formData.email,
        password: formData.password,
      });
      toast.success("Login successful!");
    } else {
      const submitData = {
        ...formData,
        graduation_year: parseInt(formData.graduation_year),
      };
      await studentAPI.register(submitData);
      toast.success("Registration successful! Welcome to CVAlign!");
    }

    navigate("/student/dashboard", { state: { email: formData.email } });
  } catch (error) {
    toast.error(error.message || (isLogin ? "Login failed" : "Registration failed"));
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="container">
      <div className="form-box">
        <div className="header">
          <h2>{isLogin ? "Student Login" : "Student Registration"}</h2>
          <p>Join CVAlign and start your career journey</p>
        </div>

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <>
              <div>
                <label htmlFor="name">Full Name *</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter your full name"
                />
              </div>
              <div>
                <label htmlFor="phone">Phone Number</label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="Enter your phone number"
                />
              </div>
              <div>
                <label htmlFor="university">University *</label>
                <input
                  type="text"
                  id="university"
                  name="university"
                  required
                  value={formData.university}
                  onChange={handleChange}
                  placeholder="Enter your university name"
                />
              </div>
              <div>
                <label htmlFor="graduation_year">Graduation Year *</label>
                <input
                  type="number"
                  id="graduation_year"
                  name="graduation_year"
                  required
                  min="2020"
                  max="2030"
                  value={formData.graduation_year}
                  onChange={handleChange}
                  placeholder="2020-2030 (inclusive) valid"
                />
              </div>
            </>
          )}

          <div>
            <label htmlFor="email">Email Address *</label>
            <input
              type="email"
              id="email"
              name="email"
              required
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
            />
          </div>

          <div>
            <label htmlFor="password">Password *</label>
            <input
              type="password"
              id="password"
              name="password"
              required
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
            />
          </div>

          <button type="submit" disabled={loading}>
            {loading ? <LoadingSpinner size="sm" /> : isLogin ? "Login" : "Create Account"}
          </button>
        </form>

        <div className="text-center" style={{ marginTop: "1.5rem" }}>
  <p className="footer-text">
    {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
    <button onClick={() => setIsLogin(!isLogin)}>
      {isLogin ? "Register here" : "Login here"}
    </button>
  </p>
</div>

      </div>
    </div>
  );
}
