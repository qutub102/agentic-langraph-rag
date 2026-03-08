/** File upload interface */
import { useState, useRef } from 'react';
import { api } from '../services/api';
import './DocumentUpload.css';

interface DocumentUploadProps {
  onUploadSuccess: (jobId: string) => void;
  onError: (error: Error) => void;
}

export function DocumentUpload({ onUploadSuccess, onError }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type !== 'application/pdf') {
        onError(new Error('Only PDF files are supported'));
        return;
      }
      if (selectedFile.size > 10 * 1024 * 1024) {
        onError(new Error('File size exceeds 10MB limit'));
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      onError(new Error('Please select a file'));
      return;
    }

    try {
      setUploading(true);
      const response = await api.ingest(file);
      onUploadSuccess(response.job_id);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      onError(err as Error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="document-upload">
      <h2>Upload Document</h2>
      <div className="upload-controls">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          disabled={uploading}
          className="file-input"
        />
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="upload-button"
        >
          {uploading ? 'Uploading...' : 'Upload Document'}
        </button>
      </div>
      {file && (
        <div className="file-info">
          Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
        </div>
      )}
    </div>
  );
}
