import axios from 'axios';
import type {
  Document,
  DocumentStats,
  DocumentUploadResponse,
  DocumentStatusResponse,
  PaginatedDocumentsResponse,
  DocumentDeleteResult,
  HealthResponse,
  SearchResult,
  SearchQuery,
  ChatRequest,
  ChatMessage,
  Chunk,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_V1_PATH = import.meta.env.VITE_API_V1_PATH || '/api/v1';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_V1_PATH}`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

export const api = {
  // ---------- Health ----------
  checkHealth: async (): Promise<HealthResponse> => {
    const res = await apiClient.get<HealthResponse>('/health');
    return res.data;
  },

  // ---------- Documents — Paginated List ----------
  getDocuments: async (params?: {
    page?: number;
    limit?: number;
    department?: string;
    language?: string;
    status?: string;
    search?: string;
  }): Promise<PaginatedDocumentsResponse> => {
    const res = await apiClient.get<PaginatedDocumentsResponse>('/documents', { params });
    return res.data;
  },

  getDocumentById: async (id: string): Promise<Document> => {
    const res = await apiClient.get<Document>(`/documents/${id}`);
    return res.data;
  },

  /** Poll document status after upload (lightweight, no full doc fetch needed). */
  getDocumentStatus: async (id: string): Promise<DocumentStatusResponse> => {
    const res = await apiClient.get<DocumentStatusResponse>(`/documents/${id}/status`);
    return res.data;
  },

  getDocumentChunks: async (documentId: string): Promise<Chunk[]> => {
    const res = await apiClient.get<Chunk[]>(`/documents/${documentId}/chunks`);
    return res.data;
  },

  deleteDocument: async (id: string): Promise<DocumentDeleteResult> => {
    const res = await apiClient.delete<DocumentDeleteResult>(`/documents/${id}`);
    return res.data;
  },

  getDocumentDownloadUrl: (id: string): string => {
    return `${API_BASE_URL}${API_V1_PATH}/documents/${id}/download`;
  },


  getStats: async (): Promise<DocumentStats> => {
    const res = await apiClient.get<DocumentStats>('/documents/stats');
    return res.data;
  },

  // ---------- Upload ----------
  /**
   * Upload a Government Resolution PDF.
   * Sends to POST /documents/upload and returns immediately with PROCESSING status.
   * Background processing (OCR → embed → Pinecone → chunks) runs server-side.
   */
  uploadDocument: async (
    formData: FormData,
    onProgress?: (progressPercent: number) => void,
  ): Promise<DocumentUploadResponse> => {
    const res = await apiClient.post<DocumentUploadResponse>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
    return res.data;
  },

  // ---------- Semantic Search ----------
  searchGR: async (
    searchParams: SearchQuery,
  ): Promise<{ results: SearchResult[]; total: number }> => {
    const res = await apiClient.post<{ results: SearchResult[]; total: number }>(
      '/search',
      searchParams,
    );
    return res.data;
  },

  // ---------- Chat / Q&A ----------
  askAI: async (chatReq: ChatRequest): Promise<ChatMessage> => {
    const res = await apiClient.post<ChatMessage>('/chat/ask', chatReq);
    return res.data;
  },
  // ---------- Demo Mode ----------
  seedDemo: async (): Promise<{ seeded: number; already_seeded: boolean; message: string }> => {
    const res = await apiClient.post<{ seeded: number; already_seeded: boolean; message: string }>('/demo/seed');
    return res.data;
  },

  resetDemo: async (): Promise<{ removed: number; message: string }> => {
    const res = await apiClient.post<{ removed: number; message: string }>('/demo/reset');
    return res.data;
  },

  getDemoStatus: async (): Promise<{ is_demo_mode: boolean; seeded_documents: number; message: string }> => {
    const res = await apiClient.get<{ is_demo_mode: boolean; seeded_documents: number; message: string }>('/demo/status');
    return res.data;
  },
};
