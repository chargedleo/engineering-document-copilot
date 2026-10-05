import { request } from './api';
import { AgentQueryRequest, AgentResponseData } from '../types';

export const agentService = {
  async queryAgent(params: AgentQueryRequest): Promise<AgentResponseData> {
    return request<AgentResponseData>('/agent/query', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch('/api/v1/health');
      if (!response.ok) return false;
      const data = await response.json();
      return data.status === 'healthy';
    } catch {
      return false;
    }
  },
};
