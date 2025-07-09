import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './EventDetails.css';
import ResponseClusterMap from './ResponseClusterMap';
import SentimentTimeline from './SentimentTimeline';
import WordCloud from './WordCloud';
import ConsensusGraph from './ConsensusGraph';

interface Inquiry {
  id: string;
  question_text: string;
  description?: string;
  response_type: string;
  is_required: boolean;
  order_index: number;
  created_at: string;
}

interface Event {
  id: string;
  title: string;
  description: string;
  event_type: string;
  status: string;
  current_participants: number;
  max_participants?: number;
  start_time?: string;
  is_public: boolean;
  created_at: string;
  inquiries: Inquiry[];
}

interface EventAnalysis {
  event_id: string;
  event_title: string;
  response_count: number;
  analysis: {
    key_themes: string[];
    common_concerns: string[];
    suggested_actions: string[];
    participant_sentiment: string;
    summary: string;
  };
  timestamp: string;
}

interface EventDetailsProps {
  eventId: string;
  userRole: 'admin' | 'user' | 'anonymous';
  onBack: () => void;
  onParticipate: () => void;
  onStartDialogue?: () => void;
  onNavigateToParticipate?: (eventId: string) => void;
  onNavigateToResults?: (eventId: string) => void;
}

const EventDetails: React.FC<EventDetailsProps> = ({ 
  eventId, 
  userRole, 
  onBack, 
  onParticipate,
  onStartDialogue,
  onNavigateToParticipate,
  onNavigateToResults
}) => {
  const [event, setEvent] = useState<Event | null>(null);
  const [analysis, setAnalysis] = useState<EventAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState<'participate' | 'results' | null>(null);

  const fetchEventDetails = async () => {
    setLoading(true);
    try {
      const response = await apiService.getEvent(eventId);
      
      if (response.error) {
        setError(response.error);
        return;
      }
      
      setEvent(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load event details');
      console.error('Error fetching event details:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchEventAnalysis = async () => {
    setAnalysisLoading(true);
    try {
      const response = await apiService.analyzeEvent(eventId);
      
      if (response.error) {
        setError(response.error);
        return;
      }
      
      setAnalysis(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load event analysis');
      console.error('Error fetching event analysis:', err);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const copyToClipboard = async (text: string, type: 'participate' | 'results') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedLink(type);
      setTimeout(() => setCopiedLink(null), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const getParticipateLink = () => {
    const baseUrl = window.location.origin;
    return `${baseUrl}/participate/${eventId}`;
  };

  const getResultsLink = () => {
    const baseUrl = window.location.origin;
    return `${baseUrl}/results/${eventId}`;
  };

  useEffect(() => {
    fetchEventDetails();
    fetchEventAnalysis();
  }, [eventId]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'active': return 'status-badge active';
      case 'draft': return 'status-badge draft';
      case 'completed': return 'status-badge completed';
      case 'cancelled': return 'status-badge cancelled';
      default: return 'status-badge';
    }
  };

  if (loading) {
    return (
      <div className="event-details-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading event details...</p>
        </div>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="event-details-container">
        <div className="error-state">
          <h3>Error Loading Event</h3>
          <p>{error || 'Event not found'}</p>
          <button className="btn-primary" onClick={onBack}>
            Back to Events
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="event-details-container">
      {/* Header */}
      <div className="event-details-header">
        <button className="back-button" onClick={onBack}>
          ← Back to Events
        </button>
        <div className="header-content">
          <div className="event-title-section">
            <h1>{event.title}</h1>
            <span className={getStatusBadgeClass(event.status)}>
              {event.status}
            </span>
          </div>
          <p className="event-description">{event.description}</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <div className="action-buttons">
          {event.status === 'active' && (
            <>
              <button className="btn-primary" onClick={onParticipate}>
                Participate Now
              </button>
              {onStartDialogue && (
                <button className="btn-primary" onClick={onStartDialogue}>
                  Start Dialogue Rounds
                </button>
              )}
            </>
          )}
          <button 
            className="btn-secondary"
            onClick={() => copyToClipboard(getParticipateLink(), 'participate')}
          >
            {copiedLink === 'participate' ? '✓ Copied!' : 'Copy Participate Link'}
          </button>
          <button 
            className="btn-secondary"
            onClick={() => copyToClipboard(getResultsLink(), 'results')}
          >
            {copiedLink === 'results' ? '✓ Copied!' : 'Copy Public Results Link'}
          </button>
          {onNavigateToParticipate && (
            <button 
              className="btn-secondary"
              onClick={() => onNavigateToParticipate(eventId)}
            >
              Go to Participate
            </button>
          )}
          {onNavigateToResults && (
            <button 
              className="btn-secondary"
              onClick={() => onNavigateToResults(eventId)}
            >
              View Results
            </button>
          )}
        </div>
      </div>

      {/* Event Information */}
      <div className="event-info-grid">
        <div className="info-card">
          <h3>Event Details</h3>
          <div className="info-item">
            <span className="label">Type:</span>
            <span className="value">{event.event_type}</span>
          </div>
          <div className="info-item">
            <span className="label">Participants:</span>
            <span className="value">
              {event.current_participants}
              {event.max_participants && ` / ${event.max_participants}`}
            </span>
          </div>
          <div className="info-item">
            <span className="label">Visibility:</span>
            <span className="value">{event.is_public ? 'Public' : 'Private'}</span>
          </div>
          {event.start_time && (
            <div className="info-item">
              <span className="label">Start Time:</span>
              <span className="value">{formatDate(event.start_time)}</span>
            </div>
          )}
          <div className="info-item">
            <span className="label">Created:</span>
            <span className="value">{formatDate(event.created_at)}</span>
          </div>
        </div>

        {/* AI Analysis */}
        <div className="info-card">
          <div className="card-header">
            <h3>AI Analysis</h3>
            <button 
              className="refresh-btn"
              onClick={fetchEventAnalysis}
              disabled={analysisLoading}
            >
              {analysisLoading ? '🔄' : '🔄'}
            </button>
          </div>
          
          {analysisLoading ? (
            <div className="loading-state">
              <div className="loading-spinner small"></div>
              <p>Analyzing responses...</p>
            </div>
          ) : analysis ? (
            <div className="analysis-content">
              <div className="analysis-summary">
                <p><strong>Summary:</strong> {analysis.analysis.summary}</p>
                <p><strong>Sentiment:</strong> {analysis.analysis.participant_sentiment}</p>
                <p><strong>Responses:</strong> {analysis.response_count}</p>
              </div>
              
              {Array.isArray(analysis.analysis.key_themes) && analysis.analysis.key_themes.length > 0 && (
                <div className="analysis-section">
                  <h4>Key Themes</h4>
                  <ul>
                    {analysis.analysis.key_themes.map((theme, index) => (
                      <li key={index}>{theme}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {Array.isArray(analysis.analysis.common_concerns) && analysis.analysis.common_concerns.length > 0 && (
                <div className="analysis-section">
                  <h4>Common Concerns</h4>
                  <ul>
                    {analysis.analysis.common_concerns.map((concern, index) => (
                      <li key={index}>{concern}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {Array.isArray(analysis.analysis.suggested_actions) && analysis.analysis.suggested_actions.length > 0 && (
                <div className="analysis-section">
                  <h4>Suggested Actions</h4>
                  <ul>
                    {analysis.analysis.suggested_actions.map((action, index) => (
                      <li key={index}>{action}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state">
              <p>No analysis available yet.</p>
              <p>Participate in the event to generate AI insights.</p>
            </div>
          )}
        </div>

        {/* Cluster Map Visualization */}
        {(event.status === 'active' || event.status === 'completed') && (
          <div className="info-card">
            <ResponseClusterMap eventId={eventId} />
          </div>
        )}

        {/* Sentiment Timeline Visualization */}
        {(event.status === 'active' || event.status === 'completed') && (
          <div className="info-card">
            <SentimentTimeline eventId={eventId} />
          </div>
        )}

        {/* Word Cloud Visualization */}
        {(event.status === 'active' || event.status === 'completed') && (
          <div className="info-card">
            <WordCloud eventId={eventId} />
          </div>
        )}

        {/* Consensus Graph Visualization */}
        {(event.status === 'active' || event.status === 'completed') && (
          <div className="info-card">
            <ConsensusGraph eventId={eventId} />
          </div>
        )}
      </div>

      {/* Activity Timeline - Placeholder for future implementation */}
      <div className="info-card">
        <h3>Recent Activity</h3>
        <div className="activity-timeline">
          <div className="activity-item">
            <div className="activity-icon">📝</div>
            <div className="activity-content">
              <p><strong>Event Created</strong></p>
              <p className="activity-time">{formatDate(event.created_at)}</p>
            </div>
          </div>
          {event.status === 'active' && (
            <div className="activity-item">
              <div className="activity-icon">🚀</div>
              <div className="activity-content">
                <p><strong>Event Published</strong></p>
                <p className="activity-time">Recently</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EventDetails; 