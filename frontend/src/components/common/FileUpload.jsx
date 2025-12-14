import React, { useState, useId } from 'react';
import { Upload } from 'lucide-react';

const FileUpload = ({ onFileSelect, accept, maxSize = 50, disabled = false }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const inputId = useId();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;

    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (disabled) return;

    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSize) {
      alert(`File size must be less than ${maxSize}MB`);
      return;
    }
    setSelectedFile(file);
    onFileSelect(file);
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        disabled
          ? 'border-secondary-600 bg-secondary-800/30 opacity-50 cursor-not-allowed'
          : dragActive
            ? 'border-primary-400 bg-primary-900/20'
            : 'border-secondary-600 hover:border-primary-500/50 bg-secondary-800/20'
      }`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id={inputId}
        className="hidden"
        accept={accept}
        onChange={handleChange}
        disabled={disabled}
      />
      <label htmlFor={inputId} className={disabled ? 'cursor-not-allowed' : 'cursor-pointer'}>
        <Upload className={`mx-auto h-12 w-12 ${disabled ? 'text-secondary-500' : 'text-primary-400'}`} />
        <p className="mt-2 text-sm text-primary-200">
          <span className={`font-semibold ${disabled ? 'text-secondary-400' : 'text-primary-300'}`}>
            Click to upload
          </span> or drag and drop
        </p>
        <p className="text-xs text-primary-400 mt-1">
          {accept} (max {maxSize}MB)
        </p>
      </label>
      {selectedFile && (
        <div className="mt-4 text-sm text-cyan-200">
          Selected: <span className="font-medium text-cyan-100">{selectedFile.name}</span>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
