// frontend/pages/Header.jsx
import React from "react";
import { Link, useLocation } from "react-router-dom";
import "./Header.css";

export default function Header() {
  const location = useLocation();

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">
          CVAlign
        </Link>

        <nav className="nav">
          {location.pathname === "/" && (
            <>
              <Link to="/student/register" className="nav-link">
                Student Portal
              </Link>
              <Link to="/recruiter/register" className="nav-link">
                Recruiter Portal
              </Link>
            </>
          )}

          {location.pathname.includes("/student") && (
            <Link to="/student/dashboard" className="nav-button student-btn">
              Dashboard
            </Link>
          )}

          {location.pathname.includes("/recruiter") && (
            <Link to="/recruiter/dashboard" className="nav-button recruiter-btn">
              Dashboard
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
