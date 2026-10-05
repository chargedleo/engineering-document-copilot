import { request } from './api';
import { ChatSession, ChatMessage } from '../types';

export interface ChatQueryParams {
  sessionId?: string;
  query: string;
  documentIds?: string[];
  includeCadContext?: boolean;
}

export const chatService = {
  async listSessions(limit = 20): Promise<ChatSession[]> {
    return request<ChatSession[]>(`/chat/sessions?limit=${limit}`);
  },

  async createSession(title?: string): Promise<ChatSession> {
    return request<ChatSession>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify({ title: title || 'New Engineering Inquiry' }),
    });
  },

  async getSessionHistory(sessionId: string): Promise<ChatSession> {
    return request<ChatSession>(`/chat/sessions/${sessionId}`);
  },

  async sendQuery(params: ChatQueryParams): Promise<ChatMessage> {
    return request<ChatMessage>('/chat/query', {
      method: 'POST',
      body: JSON.stringify({
        session_id: params.sessionId,
        query: params.query,
        document_ids: params.documentIds,
        include_cad_context: params.includeCadContext ?? true,
      }),
    });
  },
};
