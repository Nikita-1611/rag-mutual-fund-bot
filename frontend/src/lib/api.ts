import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  payload?: any;
}

export interface ChatQueryResponse {
  answer: string;
  source_url: string;
  last_updated: string;
  is_refusal?: boolean;
}

export interface SessionResponse {
  session_id: string;
}

export const api = {
  async initSession(): Promise<string> {
    try {
      const response = await axios.post<SessionResponse>(`${API_BASE_URL}/session/init`);
      return response.data.session_id;
    } catch (error) {
      console.error('Failed to initialize session:', error);
      throw error;
    }
  },

  async queryChat(sessionId: string, query: string): Promise<ChatQueryResponse> {
    try {
      const response = await axios.post<ChatQueryResponse>(`${API_BASE_URL}/chat/query`, {
        session_id: sessionId,
        query: query
      });
      return response.data;
    } catch (error) {
      console.error('Chat query failed:', error);
      throw error;
    }
  },

  async checkHealth(): Promise<boolean> {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      return response.data.status === 'healthy';
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
};
