/** Data fetching hook for jobs and chat */
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Job, ChatResponse } from '../types';

export function useDashboardData() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [jobsError, setJobsError] = useState<Error | null>(null);
  
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<Error | null>(null);

  // Fetch jobs on mount
  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      setJobsLoading(true);
      setJobsError(null);
      const jobList = await api.listJobs();
      setJobs(jobList);
    } catch (err) {
      setJobsError(err as Error);
    } finally {
      setJobsLoading(false);
    }
  };

  const submitQuestion = async (question: string) => {
    try {
      setChatLoading(true);
      setChatError(null);
      setChatResponse(null);
      const response = await api.chat(question);
      setChatResponse(response);
    } catch (err) {
      setChatError(err as Error);
    } finally {
      setChatLoading(false);
    }
  };

  return {
    jobs,
    jobsLoading,
    jobsError,
    fetchJobs,
    chatResponse,
    chatLoading,
    chatError,
    submitQuestion,
  };
}
