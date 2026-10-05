import { useState, useEffect, useCallback } from 'react';
import { Document, DocumentType } from '../types';
import { documentService, DocumentFilters } from '../services/documentService';

export function useDocuments(initialFilters: DocumentFilters = {}) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<DocumentFilters>(initialFilters);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await documentService.getDocuments(filters);
      setDocuments(response.items);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const uploadDocument = async (file: File, docType: DocumentType) => {
    setLoading(true);
    try {
      const newDoc = await documentService.uploadDocument(file, docType);
      await fetchDocuments();
      return newDoc;
    } catch (err: any) {
      setError(err.message || 'Failed to upload document');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    documents,
    total,
    loading,
    error,
    filters,
    setFilters,
    refresh: fetchDocuments,
    uploadDocument,
  };
}
