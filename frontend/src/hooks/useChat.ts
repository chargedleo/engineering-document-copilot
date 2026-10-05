import { useState, useCallback } from 'react';
import { ConversationTurn, AgentResponseData } from '../types';
import { agentService } from '../services/agentService';

export function useChat() {
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const sendQuery = useCallback(async (
    query: string,
    filters?: { part_number?: string; revision?: string }
  ) => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    const turnId = `turn-${Date.now()}`;
    const newTurn: ConversationTurn = {
      id: turnId,
      query: trimmed,
      timestamp: new Date().toISOString(),
      loading: true,
    };

    setTurns((prev) => [...prev, newTurn]);
    setLoading(true);
    setError(null);

    try {
      const response: AgentResponseData = await agentService.queryAgent({
        query: trimmed,
        top_k: 5,
        filters,
      });

      setTurns((prev) =>
        prev.map((t) => (t.id === turnId ? { ...t, loading: false, response } : t))
      );
    } catch (err: any) {
      const errMsg = err.message || 'Error communicating with Engineering Copilot backend.';
      setError(errMsg);
      setTurns((prev) =>
        prev.map((t) => (t.id === turnId ? { ...t, loading: false, error: errMsg } : t))
      );
    } finally {
      setLoading(false);
    }
  }, [loading]);

  const clearChat = useCallback(() => {
    setTurns([]);
    setError(null);
  }, []);

  return {
    turns,
    loading,
    error,
    sendQuery,
    clearChat,
  };
}
