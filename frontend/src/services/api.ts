/** Centralized API client with all endpoints */
import axios, { AxiosInstance } from 'axios';
import {
  IngestResponse,
  IngestStatusResponse,
  ChatResponse,
  Job,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        const message = error.response?.data?.detail || error.message || 'An error occurred';
        return Promise.reject(new Error(message));
      }
    );
  }

  async ingest(file: File, collectionName: string): Promise<IngestResponse> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const base64 = reader.result as string;
          const base64Content = base64.split(',')[1] || base64; // Remove data URL prefix if present

          const response = await this.client.post<IngestResponse>('/ingest', {
            file_name: file.name,
            file_content_base64: base64Content,
            collection_name: collectionName,
          });
          resolve(response.data);
        } catch (error) {
          reject(error);
        }
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsDataURL(file);
    });
  }

  async getJobStatus(jobId: string): Promise<IngestStatusResponse> {
    const response = await this.client.get<IngestStatusResponse>(`/ingest/${jobId}`);
    return response.data;
  }

  async listJobs(): Promise<Job[]> {
    const response = await this.client.get<Job[]>('/ingest');
    return response.data;
  }

  async chat(question: string, collectionName: string): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>('/chat', {
      question,
      collection_name: collectionName,
    });
    return response.data;
  }
}

export const api = new ApiClient();
