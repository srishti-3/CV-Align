//UPDATE DONE
import React, { useState } from "react";
import toast from "react-hot-toast";

export default function CVUpload({ onUpload, maxFiles = 3 }) {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleFiles = async (files) => {
    if (files.length === 0) return;

    const file = files[0];
    
    // Validate file type
    if (!file.type.includes('pdf')) {
      toast.error("Please upload only PDF files");
      return;
    }

    // Validate file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      toast.error("File size must be less than 5MB");
      return;
    }

    setUploading(true);
    try {
      await onUpload(file);
      toast.success("CV uploaded successfully!");
    } catch (error) {
      toast.error("Failed to upload CV");
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
        dragActive 
          ? "border-indigo-500 bg-indigo-50" 
          : "border-gray-300 hover:border-gray-400"
      }`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <div className="space-y-4">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <div>
          <p className="text-gray-600">
            <span className="font-medium text-indigo-600 hover:text-indigo-500 cursor-pointer">
              Click to upload
            </span>{" "}
            or drag and drop
          </p>
          <p className="text-sm text-gray-500">PDF files only, up to 5MB</p>
        </div>
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => handleFiles(Array.from(e.target.files))}
          disabled={uploading}
          className="hidden"
          id="cv-upload"
        />
        <label
          htmlFor="cv-upload"
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 cursor-pointer inline-block disabled:opacity-50"
        >
          {uploading ? "Uploading..." : "Choose File"}
        </label>
      </div>
    </div>
  );
}
