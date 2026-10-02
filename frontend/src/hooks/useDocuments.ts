import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import type { Document } from '../types';

export function useDocuments(params?: { department?: string; language?: string; status?: string }) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDocuments(params);
      setDocuments(data.items || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch documents');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [params?.department, params?.language, params?.status]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return { documents, loading, error, refetch: fetchDocuments };
}
