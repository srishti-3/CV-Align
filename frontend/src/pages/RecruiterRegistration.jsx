import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { recruiterAPI } from "../services/api.js";
import toast from "react-hot-toast";
import LoadingSpinner from "../components/LoadingSpinner";
import "./RecruiterRegistration.css";

export default function RecruiterAuth() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [isLogin, setIsLogin] = useState(true); // toggle form state
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    password: "",
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const resetForm = () => {
    setFormData({
      name: "",
      email: "",
      company: "",
      password: "",
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        // Login API call
        await recruiterAPI.login({
          email: formData.email,
          password: formData.password,
        });
        toast.success("Login successful! Welcome back to CVAlign!");
      } else {
        // Registration API call
        await recruiterAPI.register({
          name: formData.name,
          email: formData.email,
          company: formData.company,
          password: formData.password, 
        });
        toast.success("Registration successful! Welcome to CVAlign!");
      }

      navigate("/recruiter/dashboard", { state: { email: formData.email } });
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
          <h2>{isLogin ? "Recruiter Login" : "Recruiter Registration"}</h2>
          <p>
            {isLogin
              ? "Access your recruiter dashboard"
              : "Join CVAlign and find the best talent"}
          </p>
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
                  required={!isLogin}
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter your full name"
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

          {!isLogin && (
            <div>
              <label htmlFor="company">Company Name *</label>
              <input
                type="text"
                id="company"
                name="company"
                required={!isLogin}
                value={formData.company}
                onChange={handleChange}
                placeholder="Enter your company name"
              />
            </div>
          )}

          <div>
            <label htmlFor="password">Password *</label>
            <input
              type="password"
              id="password"
              name="password"
              required
              value={formData.password}
              onChange={handleChange}
              placeholder={isLogin ? "Enter your password" : "Create a strong password"}
            />
          </div>


          <button type="submit" disabled={loading}>
            {loading ? (
              <LoadingSpinner size="sm" />
            ) : isLogin ? (
              "Login"
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <div className="text-center" style={{ marginTop: "1.5rem" }}>
          {isLogin ? (
            <p className="footer-text">
              Don't have an account?{" "}
              <button
                onClick={() => {
                  setIsLogin(false);
                  resetForm();
                }}
              >
                Register here
              </button>
            </p>
          ) : (
            <p className="footer-text">
              Already have an account?{" "}
              <button
                onClick={() => {
                  setIsLogin(true);
                  resetForm();
                }}
              >
                Login here
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
