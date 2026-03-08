/** Polling hook for job status updates */
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { JobStatus } from '../types';

export function useJobPolling(jobId: string | null, enabled: boolean = true) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!jobId || !enabled) {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const response = await api.getJobStatus(jobId);
        setStatus(response.status);
        setError(null);

        // Stop polling if job is completed or failed
        if (response.status === 'COMPLETED' || response.status === 'FAILED') {
          clearInterval(pollInterval);
        }
      } catch (err) {
        setError(err as Error);
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds

    // Initial fetch
    api.getJobStatus(jobId)
      .then((response) => {
        setStatus(response.status);
        if (response.status === 'COMPLETED' || response.status === 'FAILED') {
          clearInterval(pollInterval);
        }
      })
      .catch((err) => {
        setError(err as Error);
        clearInterval(pollInterval);
      });

    // Cleanup
    return () => {
      clearInterval(pollInterval);
    };
  }, [jobId, enabled]);

  return { status, error };
}
