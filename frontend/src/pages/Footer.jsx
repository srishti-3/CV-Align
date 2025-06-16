// frontend/pages/Footer.jsx
import React from "react";
import "./Footer.css";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-text">
          © {new Date().getFullYear()} CVAlign — Connecting Talent with Opportunity
        </div>
      </div>
    </footer>
  );
}
