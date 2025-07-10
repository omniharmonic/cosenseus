// API service for connecting to the local backend

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface EventTemplate {
  id: string;
  name: string;
  description: string;
  event_data: any;
  created_at: string;
  updated_at: string;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Add session code to headers if available
    const sessionCode = localStorage.getItem('cosenseus_session_code');
    const authHeaders: HeadersInit = sessionCode ? { 'X-Session-Code': sessionCode } : {};

    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, { ...defaultOptions, ...options });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const detail = errorData.detail || `HTTP error! status: ${response.status}`;
        console.error(`API request failed for ${endpoint}:`, detail);
        return { error: detail };
      }
      
      if (response.status === 204) {
        return { data: undefined };
      }

      const data = await response.json();
      return { data };

    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      return { error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  // Session Management
  async createSession(displayName: string): Promise<ApiResponse<any>> {
    return this.request('/auth/session/create', {
      method: 'POST',
      body: JSON.stringify({ display_name: displayName }),
    });
  }

  async loginWithSession(sessionCode: string): Promise<ApiResponse<any>> {
    return this.request('/auth/session/login', {
      method: 'POST',
      body: JSON.stringify({ session_code: sessionCode }),
    });
  }

  async getDashboardEvents(): Promise<ApiResponse<any>> {
    return this.request('/events/dashboard');
  }

  // Health check
  async checkHealth(): Promise<ApiResponse<any>> {
    return this.request('/health');
  }

  // Events
  async getEvents(): Promise<ApiResponse<any[]>> {
    return this.request('/events');
  }

  async getEvent(eventId: string): Promise<ApiResponse<any>> {
    return this.request(`/events/${eventId}`);
  }

  async createEvent(eventData: any): Promise<ApiResponse<any>> {
    return this.request('/events', {
      method: 'POST',
      body: JSON.stringify(eventData),
    });
  }

  async updateEvent(eventId: string, eventData: any): Promise<ApiResponse<any>> {
    return this.request(`/events/${eventId}`, {
      method: 'PUT',
      body: JSON.stringify(eventData),
    });
  }

  async deleteEvent(eventId: string): Promise<ApiResponse<void>> {
    return this.request(`/events/${eventId}`, {
      method: 'DELETE',
    });
  }

  // Event participation
  async joinEvent(eventId: string, participantData: any): Promise<ApiResponse<any>> {
    return this.request(`/events/${eventId}/join`, {
      method: 'POST',
      body: JSON.stringify(participantData),
    });
  }

  async getEventParticipants(eventId: string): Promise<ApiResponse<any[]>> {
    return this.request(`/events/${eventId}/participants`);
  }

  // Responses
  async submitResponse(responseData: any): Promise<ApiResponse<any>> {
    return this.request('/responses/', {
      method: 'POST',
      body: JSON.stringify(responseData),
    });
  }

  async getEventResponses(eventId: string): Promise<ApiResponse<any>> {
    return this.request(`/events/${eventId}/responses`);
  }

  async getEventInquiries(eventId: string): Promise<ApiResponse<any>> {
    return this.request(`/inquiries/event/${eventId}`);
  }

  async getEventRoundResults(eventId: string, roundNumber?: number): Promise<ApiResponse<any[]>> {
    let url = `/events/${eventId}/round-results`;
    if (roundNumber) {
      const params = new URLSearchParams({ round_number: roundNumber.toString() });
      url += `?${params.toString()}`;
    }
    return this.request(url, { method: 'GET' });
  }

  async submitRoundResponses(responses: any[]): Promise<ApiResponse<any>> {
    return this.request('/responses/batch', {
      method: 'POST',
      body: JSON.stringify(responses),
    });
  }

  async analyzeEventRound(eventId: string, roundNumber: number): Promise<ApiResponse<any>> {
    return this.request(`/ai/analyze-event/${eventId}/round/${roundNumber}`, {
      method: 'POST',
    });
  }

  // AI Analysis
  async analyzeEvent(eventId: string): Promise<ApiResponse<any>> {
    return this.request(`/ai/analyze-event/${eventId}`, {
      method: 'POST',
    });
  }

  async getEventSummary(eventId: string): Promise<ApiResponse<any>> {
    return this.request(`/ai/event-summary/${eventId}`);
  }

  async analyzeSentiment(text: string): Promise<ApiResponse<any>> {
    return this.request(`/ai/sentiment-analysis?text=${encodeURIComponent(text)}`, {
      method: 'POST',
    });
  }

  async clusterResponses(responses: string[], numClusters: number = 3): Promise<ApiResponse<any>> {
    return this.request('/ai/cluster-responses', {
      method: 'POST',
      body: JSON.stringify({
        responses: responses,
        num_clusters: numClusters
      }),
    });
  }

  async getAiHealth(): Promise<ApiResponse<any>> {
    return this.request('/ai/health');
  }

  async getAvailableModels(): Promise<ApiResponse<any>> {
    return this.request('/ai/models');
  }

  async getSentimentTimeline(eventId: string): Promise<ApiResponse<any>> {
    return this.request(`/ai/sentiment-timeline/${eventId}`);
  }

  async getWordCloud(eventId: string): Promise<ApiResponse<any>> {
    return this.request(`/ai/word-cloud/${eventId}`);
  }

  async getConsensusGraph(eventId: string): Promise<ApiResponse<any>> {
    return this.request(`/ai/consensus-graph/${eventId}`);
  }

  async getPolisAnalysis(eventId: string, roundNumber: number): Promise<ApiResponse<any>> {
    return this.request(`/ai/polis-analysis/${eventId}/${roundNumber}`);
  }

  async getEventRoundState(eventId: string): Promise<ApiResponse<any>> {
    return this.request(`/events/${eventId}/round-state`);
  }

  async advanceEventRound(eventId: string): Promise<ApiResponse<any>> {
    return this.request(`/events/${eventId}/next-round`, { method: 'POST' });
  }

  // Dialogue Moderation
  async getSynthesisForReview(eventId: string, roundNumber: number): Promise<ApiResponse<any>> {
    return this.request(`/ai/synthesis-review/${eventId}/${roundNumber}`);
  }

  async updateSynthesis(synthesisId: string, data: { next_round_prompts: any }): Promise<ApiResponse<any>> {
    return this.request(`/ai/synthesis-review/${synthesisId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async approveSynthesis(synthesisId: string): Promise<ApiResponse<any>> {
    return this.request(`/ai/synthesis-review/${synthesisId}/approve`, {
      method: 'POST',
    });
  }

  // Event Templates
  async getEventTemplates(): Promise<ApiResponse<EventTemplate[]>> {
    return this.request('/templates/events');
  }

  async createEventTemplate(templateData: Partial<EventTemplate>): Promise<ApiResponse<EventTemplate>> {
    return this.request('/templates/events', {
      method: 'POST',
      body: JSON.stringify(templateData),
    });
  }

  async updateEventTemplate(templateId: string, templateData: Partial<EventTemplate>): Promise<ApiResponse<EventTemplate>> {
    return this.request(`/templates/events/${templateId}`, {
      method: 'PUT',
      body: JSON.stringify(templateData),
    });
  }

  async deleteEventTemplate(templateId: string): Promise<ApiResponse<void>> {
    return this.request(`/templates/events/${templateId}`, {
      method: 'DELETE',
    });
  }

  // Local development status
  async getLocalStatus(): Promise<ApiResponse<any>> {
    return this.request('/local/status');
  }

  async publishEvent(eventId: string): Promise<ApiResponse<any>> {
    return this.request(`/events/${eventId}/publish`, {
      method: 'POST',
    });
  }
}

export const apiService = new ApiService();
export default ApiService; 