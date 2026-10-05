import { request } from './api';
import { Document, DocumentPage, PaginatedResponse, DocumentStatus, DocumentCreateInput, CadMetadata } from '../types';

export interface DocumentFilters {
  page?: number;
  pageSize?: number;
  documentType?: string;
  partNumber?: string;
  status?: DocumentStatus;
  search?: string;
}

export const documentService = {
  async getDocuments(filters: DocumentFilters = {}): Promise<PaginatedResponse<Document>> {
    const params = new URLSearchParams();
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.pageSize) params.append('page_size', filters.pageSize.toString());
    if (filters.documentType) params.append('document_type', filters.documentType);
    if (filters.partNumber) params.append('part_number', filters.partNumber);
    if (filters.status) params.append('status', filters.status);
    if (filters.search) params.append('search', filters.search);

    const query = params.toString() ? `?${params.toString()}` : '';
    return request<PaginatedResponse<Document>>(`/documents${query}`);
  },

  async getDocumentById(id: string): Promise<Document> {
    return request<Document>(`/documents/${id}`);
  },

  async createDocument(data: DocumentCreateInput): Promise<Document> {
    return request<Document>('/documents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async uploadDocument(file: File, documentType = 'SPECIFICATION', partNumber?: string, revision = 'A'): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    if (partNumber) formData.append('part_number', partNumber);
    formData.append('revision', revision);

    return request<Document>('/documents/upload', {
      method: 'POST',
      body: formData,
    });
  },

  async getCadMetadataByDocument(documentId: string): Promise<CadMetadata[]> {
    return request<CadMetadata[]>(`/cad/by-document/${documentId}`);
  },

  async getDocumentPages(documentId: string, page = 1, pageSize = 50): Promise<PaginatedResponse<DocumentPage>> {
    return request<PaginatedResponse<DocumentPage>>(`/documents/${documentId}/pages?page=${page}&page_size=${pageSize}`);
  },

  async getDocumentPage(documentId: string, pageNumber: number): Promise<DocumentPage> {
    return request<DocumentPage>(`/documents/${documentId}/pages/${pageNumber}`);
  },
};
