//UPDATE DONE
// src/pages/JobDetails.jsx
import React from 'react';
import { useParams } from 'react-router-dom';

const JobDetails = () => {
  const { jobId } = useParams();

  return (
    <div className="p-4 max-w-4xl mx-auto bg-white rounded shadow-md mt-10">
      <h1 className="text-2xl font-semibold mb-4">Job Details</h1>
      <p className="text-gray-700">Displaying details for Job ID: <strong>{jobId}</strong></p>
    </div>
  );
};

export default JobDetails;
