/** Main application page */
import { useState, useEffect } from 'react';
import { DocumentUpload } from '../components/DocumentUpload';
import { JobStatusList } from '../components/JobStatusList';
import { ChatInterface } from '../components/ChatInterface';
import { useDashboardData } from '../hooks/useDashboardData';
import './Dashboard.css';

export function Dashboard() {
  const {
    jobs,
    jobsLoading,
    jobsError,
    fetchJobs,
    chatResponse,
    chatLoading,
    chatError,
    submitQuestion,
  } = useDashboardData();

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [collectionName, setCollectionName] = useState('document_chunks');

  useEffect(() => {
    document.title = 'Agentic Document Assistant';
  }, []);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const handleUploadSuccess = () => {
    setToast({ message: 'Document processed and ready for questions.', type: 'success' });
    fetchJobs(); // Refresh job list
  };

  const handleUploadError = (error: Error) => {
    setToast({ message: error.message, type: 'error' });
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Agentic Document Assistant</h1>
      </header>

      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.message}
        </div>
      )}

      {/* <div className="collection-selector">
        <label htmlFor="collection-name">Active Collection: </label>
        <input
          id="collection-name"
          type="text"
          value={collectionName}
          onChange={(e) => setCollectionName(e.target.value)}
          placeholder="e.g. resumes, docs, knowledge_base"
          pattern="[a-zA-Z0-9_-]+"
          title="Only alphanumeric characters, underscores, and dashes allowed"
        />
      </div> */}

      <main className="dashboard-content">
        <div className="dashboard-section">
          <DocumentUpload
            collectionName={collectionName}
            onUploadSuccess={handleUploadSuccess}
            onError={handleUploadError}
          />
        </div>

        <div className="dashboard-section">
          <JobStatusList
            jobs={jobs}
            loading={jobsLoading}
            error={jobsError}
            onRefresh={fetchJobs}
          />
        </div>

        <div className="dashboard-section">
          <ChatInterface
            collectionName={collectionName}
            onSubmit={submitQuestion}
            response={chatResponse}
            loading={chatLoading}
            error={chatError}
          />
        </div>
      </main>
    </div>
  );
}
