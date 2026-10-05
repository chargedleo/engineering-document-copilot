import { useState, useCallback } from 'react';
import { ChatMessage, ChatSession } from '../types';
import { chatService } from '../services/chatService';

export function useChat() {
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const startNewSession = useCallback(async (title?: string) => {
    setLoading(true);
    setError(null);
    try {
      const session = await chatService.createSession(title);
      setCurrentSession(session);
      setMessages([]);
      return session;
    } catch (err: any) {
      setError(err.message || 'Failed to initialize session');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSession = useCallback(async (sessionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const session = await chatService.getSessionHistory(sessionId);
      setCurrentSession(session);
      setMessages(session.messages || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load conversation');
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = async (query: string, includeCadContext = true) => {
    if (!query.trim()) return;

    // Optimistically add user query to state
    const optimisticUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: currentSession?.id || '',
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMsg]);
    setLoading(true);

    try {
      const assistantMsg = await chatService.sendQuery({
        sessionId: currentSession?.id,
        query,
        includeCadContext,
      });

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.message || 'Failed to receive copilot response');
    } finally {
      setLoading(false);
    }
  };

  return {
    currentSession,
    messages,
    loading,
    error,
    startNewSession,
    loadSession,
    sendMessage,
  };
}
