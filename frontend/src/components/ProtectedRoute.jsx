//UPDATE DONE
import React from "react";
import { Navigate } from "react-router-dom";

export default function ProtectedRoute({ children, userType, userEmail }) {
  if (!userEmail) {
    return <Navigate to="/" replace />;
  }

  return children;
}
