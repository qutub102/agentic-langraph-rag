/** TypeScript interfaces matching backend Pydantic models */

export type JobStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface IngestRequest {
  file_name: string;
  file_content_base64: string;
}

export interface IngestResponse {
  job_id: string;
  status: "PENDING";
}

export interface IngestStatusResponse {
  job_id: string;
  status: JobStatus;
}

export interface Job {
  job_id: string;
  file_name: string;
  status: JobStatus;
  created_at: string | null;
  updated_at: string | null;
  chunk_count: number;
  error_message: string | null;
}

export interface Citation {
  chunk_id: string;
  source: string;
  quote: string;
}

export interface ChatRequest {
  question: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  confidence: "LOW" | "MEDIUM" | "HIGH";
}
