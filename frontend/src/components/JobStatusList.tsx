/** List of ingestion jobs with status */
import { useEffect } from 'react';
import { Job, JobStatus } from '../types';
import './JobStatusList.css';

interface JobStatusListProps {
  jobs: Job[];
  loading: boolean;
  error: Error | null;
  onRefresh: () => void;
}

export function JobStatusList({ jobs, loading, error, onRefresh }: JobStatusListProps) {
  // Poll for active jobs
  const activeJobIds = jobs
    .filter((job) => job.status === 'PENDING' || job.status === 'PROCESSING')
    .map((job) => job.job_id);

  // Refresh when active jobs complete
  useEffect(() => {
    if (activeJobIds.length > 0) {
      const interval = setInterval(() => {
        onRefresh();
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [activeJobIds.length, onRefresh]);

  const getStatusColor = (status: JobStatus): string => {
    switch (status) {
      case 'PENDING':
        return '#ffc107';
      case 'PROCESSING':
        return '#17a2b8';
      case 'COMPLETED':
        return '#28a745';
      case 'FAILED':
        return '#dc3545';
      default:
        return '#6c757d';
    }
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch {
      return 'N/A';
    }
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="job-status-list">
        <h2>Job Status</h2>
        <div className="loading-skeleton">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton-row" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="job-status-list">
      <div className="job-header">
        <h2>Job Status</h2>
        <button onClick={onRefresh} className="refresh-button">
          Refresh
        </button>
      </div>
      {error && (
        <div className="error-message">
          Error loading jobs: {error.message}
        </div>
      )}
      {jobs.length === 0 ? (
        <div className="empty-state">No jobs yet. Upload a document to get started.</div>
      ) : (
        <div className="jobs-table">
          <div className="table-header">
            <div className="col-file-name">File Name</div>
            <div className="col-status">Status</div>
            <div className="col-chunks">Chunks</div>
            <div className="col-date">Created</div>
          </div>
          {jobs.map((job) => (
            <div key={job.job_id} className="table-row">
              <div className="col-file-name">{job.file_name}</div>
              <div className="col-status">
                <span
                  className="status-badge"
                  style={{ backgroundColor: getStatusColor(job.status) }}
                >
                  {job.status}
                </span>
              </div>
              <div className="col-chunks">{job.chunk_count}</div>
              <div className="col-date">{formatDate(job.created_at)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
