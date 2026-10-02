export type Language = 'mr' | 'hi' | 'en';

export type DocumentStatus = 'PROCESSING' | 'COMPLETED' | 'INDEXED' | 'FAILED';

export interface Document {
  id: string; // uuid
  filename: string;
  original_filename: string;
  storage_path: string;
  status: DocumentStatus;
  category: string | null;
  department: string | null;
  language: string | null;
  document_type: string | null;
  subject: string | null;
  gr_number: string | null;
  pages: number | null;
  chunk_count: number | null;
  uploaded_at: string;
}

export interface DocumentUploadResponse {
  id: string;
  filename: string;
  original_filename: string;
  storage_path: string;
  status: DocumentStatus;
  message: string;
}

export interface DocumentStatusResponse {
  id: string;
  status: DocumentStatus;
  pages: number | null;
  chunk_count: number | null;
  uploaded_at: string;
}

export interface PaginatedDocumentsResponse {
  items: Document[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface DocumentDeleteResult {
  success: boolean;
  document_id: string;
  message: string;
  storage_deleted: boolean;
  vectors_deleted: number;
  chunks_removed: number;
}

export interface Chunk {
  id: string; // uuid
  chunk_id: string;
  document_id: string; // uuid
  page: number | null;
  section: string | null;
  pinecone_id: string;
  created_at: string;
}

export interface Citation {
  document_id: string;
  document_title: string;
  gr_number?: string | null;
  department?: string | null;
  page?: number | null;
  section?: string | null;
  snippet: string;
  score: number;
}

export interface SearchResult {
  chunk_id: string;
  pinecone_id: string;
  document_id: string;
  score: number;
  text: string;
  page: number | null;
  section: string | null;
  document?: Document;
}

export interface SearchQuery {
  query: string;
  language?: Language;
  top_k?: number;
  department?: string;
  category?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  answer?: string;
  language?: Language;
  citations?: Citation[];
  insufficient_evidence?: boolean;
  timestamp: string;
}

export interface ChatRequest {
  query: string;
  language: Language;
  history?: Array<{ role: string; content: string }>;
  top_k?: number;
  department?: string;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  is_demo_mode?: boolean;
  timestamp: string;
  services: {
    supabase_db: boolean;
    supabase_storage: boolean;
    pinecone: boolean;
    gemini_api: boolean;
  };
}

export interface DocumentStats {
  total_documents: number;
  total_chunks: number;
  completed_documents: number;
  indexed_documents: number; // alias for completed_documents (backwards compat)
  processing_documents: number;
  failed_documents: number;
  departments_count: number;
  language_breakdown: Record<string, number>;
}
