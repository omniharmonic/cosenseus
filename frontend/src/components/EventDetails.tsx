import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './EventDetails.css';
import ResponseClusterMap from './ResponseClusterMap';
import SentimentTimeline from './SentimentTimeline';
import WordCloud from './WordCloud';
import ConsensusGraph from './ConsensusGraph';
import DialogueModeration from './DialogueModeration';

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
  organizer_id: string; // This field is now required from backend
}

interface EventAnalysis {
  event_id: string;
  event_title: string;
  response_count: number;
  analysis: {
    key_themes: string[];
    common_concerns: string[];
    suggested_actions: string[];
    consensus_points: string[];
    dialogue_opportunities: string[];
    common_desired_outcomes: string[];
    common_strategies: string[];
    common_values: string[];
    participant_sentiment: string;
    summary: string;
  };
  timestamp: string;
}

interface EventDetailsProps {
  eventId: string;
  user: { id: string; role: 'admin' | 'user' | 'anonymous'; display_name: string; session_code: string; created_at: string } | null;
  onBack: () => void;
  onParticipate: () => void;
  onStartDialogue?: () => void;
  onNavigateToParticipate?: (eventId: string) => void;
  onNavigateToResults?: (eventId: string) => void;
}

interface RoundState {
  current_round: number;
  status: string;
}

interface ExportOptions {
  type: 'raw_data' | 'proposal' | 'agreement' | 'synthesis' | 'roadmap';
  format: 'json' | 'csv' | 'markdown';
  include_analysis: boolean;
}

const EventDetails: React.FC<EventDetailsProps> = ({ 
  eventId, 
  user, 
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
  const [isPublishing, setIsPublishing] = useState(false);
  const [copiedLink, setCopiedLink] = useState<'participate' | 'results' | null>(null);
  const [roundState, setRoundState] = useState<RoundState | null>(null);
  const [isAdvancingRound, setIsAdvancingRound] = useState(false);
  const [analysisStep, setAnalysisStep] = useState<string | null>(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [isEndingDialogue, setIsEndingDialogue] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    type: 'raw_data',
    format: 'json',
    include_analysis: true
  });
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

  // Debug logging (only when REACT_APP_DEBUG is enabled)
  useEffect(() => {
    if (process.env.NODE_ENV === 'development' && process.env.REACT_APP_DEBUG === 'true') {
      console.log('🔍 EventDetails Debug Info:');
      console.log('- user object:', user);
      console.log('- user.role:', user?.role);
      console.log('- user.id:', user?.id);
      console.log('- eventId:', eventId);

      // Additional debugging: check if event data exists and log organizer info
      if (event) {
        console.log('- Event organizer_id:', event.organizer_id || 'No organizer_id in event');
        console.log('- Event data:', event);
        console.log('- Is current user organizer?', event.organizer_id === user?.id);
        console.log('- Is current user admin?', user?.role === 'admin');
      }
    }
  }, [user, eventId, event]);

  // Helper function to check if current user is admin/organizer
  const isCurrentUserAdmin = () => {
    const debugEnabled = process.env.NODE_ENV === 'development' && process.env.REACT_APP_DEBUG === 'true';

    if (!user || !event) {
      if (debugEnabled) console.log('❌ No user or event data available');
      return false;
    }

    // Check 1: Global admin role
    if (user.role === 'admin') {
      if (debugEnabled) console.log('✅ User is admin via global role');
      return true;
    }

    // Check 2: Event organizer
    if (event.organizer_id && event.organizer_id === user.id) {
      if (debugEnabled) console.log('✅ User is event organizer');
      return true;
    }

    if (debugEnabled) {
      console.log('❌ User is neither admin nor organizer');
      console.log('- User role:', user.role);
      console.log('- User ID:', user.id);
      console.log('- Event organizer_id:', event.organizer_id);
    }
    return false;
  };

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

  const fetchRoundState = async () => {
    try {
      const response = await apiService.getEventRoundState(eventId);
      if (response.data) {
        setRoundState(response.data);
        return response.data;
      }
    } catch (err) {
      console.error('Failed to fetch round state:', err);
      // We don't need to show an error for this, as it's for admins mostly
    }
    return null;
  };

  const handleAdvanceRound = async () => {
    if (!isCurrentUserAdmin()) return;

    setIsAdvancingRound(true);
    setAnalysisStep('Initiating analysis...');
    
    try {
      const response = await apiService.advanceEventRound(eventId);
      if (response.error) {
        setError(response.error);
        setIsAdvancingRound(false);
        setAnalysisStep('');
        return;
      }

      // Start polling for round state changes
      setAnalysisStep('Processing responses...');
      
      const pollForCompletion = async () => {
        const updatedRoundState = await fetchRoundState();
        
        if (updatedRoundState?.status === 'admin_review') {
          // Analysis complete, ready for moderation
          setAnalysisStep('Analysis complete! Loading moderation interface...');
          if (pollInterval) {
            clearInterval(pollInterval);
            setPollInterval(null);
          }
          setIsAdvancingRound(false);
          setAnalysisStep('');
          return;
        }
        
        // Update progress message
        setAnalysisStep('AI analysis in progress...');
      };

      // Poll every 3 seconds
      const interval = setInterval(pollForCompletion, 3000);
      setPollInterval(interval);
      
      // Initial check
      pollForCompletion();
      
      // Timeout after 2 minutes
      setTimeout(() => {
        if (pollInterval) {
          clearInterval(pollInterval);
          setPollInterval(null);
          setIsAdvancingRound(false);
          setAnalysisStep('');
          setError('Analysis is taking longer than expected. Please refresh the page to check status.');
        }
      }, 120000);

    } catch (err) {
      setError('Failed to advance to the next round.');
      console.error('Error advancing round:', err);
      setIsAdvancingRound(false);
      setAnalysisStep('');
    }
  };

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [pollInterval]);

  const handlePublish = async () => {
    if (!isCurrentUserAdmin() || !event || event.status !== 'draft') return;

    setIsPublishing(true);
    try {
      const response = await apiService.publishEvent(eventId);
      if (response.error) {
        setError(response.error);
      } else {
        // Re-fetch event details to update the status and UI
        await fetchEventDetails();
      }
    } catch (err) {
      setError('Failed to publish the event.');
      console.error('Error publishing event:', err);
    } finally {
      setIsPublishing(false);
    }
  };

  const handleEndDialogue = async () => {
    if (!event || !isCurrentUserAdmin()) return;
    
    const confirmEnd = window.confirm(
      'Are you sure you want to end this dialogue? This will mark the event as completed and no further rounds can be added.'
    );
    
    if (!confirmEnd) return;
    
    setIsEndingDialogue(true);
    
    try {
      const sessionCode = localStorage.getItem('cosenseus_session_code');
      const response = await fetch(`/api/v1/events/${eventId}/end-dialogue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Code': sessionCode || ''
        }
      });

      if (response.ok) {
        const result = await response.json();
        setEvent(prev => prev ? { ...prev, status: 'completed' } : null);
        
        // Show success notification but don't auto-open export modal
        alert(`Dialogue ended successfully! Results are ready for export. Final round: ${result.final_round}`);
      } else {
        const errorData = await response.json();
        alert(`Failed to end dialogue: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err: any) {
      alert(`Error ending dialogue: ${err.message}`);
    } finally {
      setIsEndingDialogue(false);
    }
  };

  const handleExport = async () => {
    if (!event) return;
    
    setIsExporting(true);
    
    try {
      const sessionCode = localStorage.getItem('cosenseus_session_code');
      const response = await fetch(`/api/v1/events/${eventId}/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Code': sessionCode || ''
        },
        body: JSON.stringify(exportOptions)
      });

      if (response.ok) {
        const exportResult = await response.json();
        
        // Create and download file
        const blob = new Blob([exportResult.content], { 
          type: exportOptions.format === 'json' ? 'application/json' : 'text/plain' 
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = exportResult.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        alert('Export downloaded successfully!');
        setShowExportModal(false);
      } else {
        const errorData = await response.json();
        alert(`Export failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err: any) {
      alert(`Export error: ${err.message}`);
    } finally {
      setIsExporting(false);
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

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);

    // 1. Fetch event details first
    const eventResponse = await apiService.getEvent(eventId);

    if (eventResponse.error) {
      // If event not found or other error, stop here and set error state
      setError(eventResponse.error);
      setLoading(false);
      return;
    }

    setEvent(eventResponse.data);

    // 2. If event details are successfully fetched, fetch analysis and round state
    setAnalysisLoading(true);
    const analysisResponse = await apiService.getEventSummary(eventId); // Switched to a more appropriate summary endpoint
    if (analysisResponse.data) {
      setAnalysis(analysisResponse.data);
    }
    // Don't set a primary error if only analysis fails, but we could show a secondary indicator
    if (analysisResponse.error) {
      console.warn("Could not load event analysis:", analysisResponse.error);
    }
    setAnalysisLoading(false);

    if (isCurrentUserAdmin()) {
      await fetchRoundState();
    }

    setLoading(false);
  };
  
  useEffect(() => {
    fetchEventDetails();
    fetchAllData();
    
    if (isCurrentUserAdmin()) {
      fetchRoundState();
    }
  }, [eventId]);

  if (isCurrentUserAdmin() && roundState && roundState.status === 'admin_review') {
    return (
      <DialogueModeration 
        eventId={eventId}
        roundNumber={roundState.current_round}
        onApprovalSuccess={fetchAllData}
      />
    );
  }

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

  if (error && !event) {
    return (
      <div className="event-details-container">
        <div className="error-state">
          <h3>{error.includes('Not Found') ? 'Event Not Found' : 'Error Loading Event'}</h3>
          <p>{error.includes('Not Found') ? 'The event you are looking for does not exist. It may have been deleted.' : error}</p>
          <button className="btn btn-primary" onClick={onBack}>
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="event-details-container">
        <div className="error-state">
          <h3>Event Data Not Available</h3>
          <p>The event data could not be loaded, but no specific error was reported. Please try again later.</p>
          <button className="btn btn-primary" onClick={onBack}>
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="event-details-container">
      {/* Header */}
      <div className="event-details-header">
        <button className="btn btn-secondary back-button" onClick={onBack}>
          &larr; Back to Dashboard
        </button>
        <div className="header-content">
          <div className="event-title-section">
            <h1>{event.title}</h1>
            <span className={getStatusBadgeClass(event.status)}>
              {event.status.charAt(0).toUpperCase() + event.status.slice(1)}
            </span>
          </div>
          <p className="event-description">{event.description}</p>
        </div>
      </div>
      
      {/* Quick Actions */}
      <div className="quick-actions">
        <div className="action-buttons">
          {isCurrentUserAdmin() && event.status === 'draft' && (
            <button
              className="btn btn-primary"
              onClick={handlePublish}
              disabled={isPublishing}
            >
              {isPublishing ? 'Publishing...' : 'Publish Event'}
            </button>
          )}

          {event.status === 'active' && user?.role !== 'admin' && (
            <button className="btn btn-primary" onClick={onParticipate}>
              Participate Now
            </button>
          )}
          
          {/* --- Admin Dialogue Controls --- */}
          {isCurrentUserAdmin() && event.status === 'active' && (
            <>
              {!roundState && (
                <button className="btn btn-primary" onClick={handleAdvanceRound} disabled={isAdvancingRound}>
                  {isAdvancingRound ? (analysisStep || 'Starting...') : 'Start Dialogue'}
                </button>
              )}
              {roundState?.status === 'waiting_for_responses' && (
                <button 
                  className="btn btn-primary" 
                  onClick={handleAdvanceRound}
                  disabled={isAdvancingRound}
                >
                  {isAdvancingRound ? (analysisStep || 'Processing...') : 'End Round & Start Analysis'}
                </button>
              )}
              {isAdvancingRound && analysisStep && (
                <div className="analysis-progress">
                  <div className="loading-spinner small"></div>
                  <span>{analysisStep}</span>
                </div>
              )}
              {/* End Dialogue Button */}
              <button 
                className="btn btn-warning end-dialogue-btn"
                onClick={handleEndDialogue}
                disabled={isEndingDialogue}
              >
                {isEndingDialogue ? 'Ending...' : 'End Dialogue'}
              </button>
            </>
          )}

          {/* Export Button for Completed Events */}
          {isCurrentUserAdmin() && event.status === 'completed' && (
            <button 
              className="btn btn-success export-btn"
              onClick={() => setShowExportModal(true)}
            >
              📋 Export Results
            </button>
          )}

          <button 
            className="btn btn-secondary"
            onClick={() => copyToClipboard(getParticipateLink(), 'participate')}
          >
            {copiedLink === 'participate' ? '✓ Copied!' : 'Copy Participate Link'}
          </button>
          <button 
            className="btn btn-secondary"
            onClick={() => copyToClipboard(getResultsLink(), 'results')}
          >
            {copiedLink === 'results' ? '✓ Copied!' : 'Copy Public Results Link'}
          </button>
          {onNavigateToParticipate && (
            <button 
              className="btn btn-secondary"
              onClick={() => onNavigateToParticipate(eventId)}
            >
              Go to Participate
            </button>
          )}
          {onNavigateToResults && (
            <button 
              className="btn btn-secondary"
              onClick={() => onNavigateToResults(eventId)}
            >
              View Results
            </button>
          )}
        </div>
        
        {isCurrentUserAdmin() && roundState?.status === 'admin_review' && (
          <div className="moderation-section">
            <DialogueModeration eventId={eventId} roundNumber={roundState.current_round} onApprovalSuccess={fetchAllData} />
          </div>
        )}
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <div className="modal-overlay">
          <div className="modal-content export-modal">
            <h3>Export Event Results</h3>
            <p>Choose what type of export you'd like to generate:</p>
            
            <div className="export-options">
              <div className="option-group">
                <label>Export Type:</label>
                <select 
                  value={exportOptions.type}
                  onChange={(e) => setExportOptions(prev => ({...prev, type: e.target.value as any}))}
                >
                  <option value="raw_data">Raw Data (all responses and analysis)</option>
                  <option value="synthesis">Synthesis Report (comprehensive summary)</option>
                  <option value="proposal">Proposal Document (AI-generated proposal)</option>
                  <option value="agreement">Agreement Document (consensus points)</option>
                  <option value="roadmap">Implementation Roadmap (action plan)</option>
                </select>
              </div>

              <div className="option-group">
                <label>Format:</label>
                <select 
                  value={exportOptions.format}
                  onChange={(e) => setExportOptions(prev => ({...prev, format: e.target.value as any}))}
                >
                  <option value="markdown">Markdown (.md)</option>
                  <option value="json">JSON (.json)</option>
                  {exportOptions.type === 'raw_data' && <option value="csv">CSV (.csv)</option>}
                </select>
              </div>

              <div className="option-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={exportOptions.include_analysis}
                    onChange={(e) => setExportOptions(prev => ({...prev, include_analysis: e.target.checked}))}
                  />
                  Include AI analysis data
                </label>
              </div>
            </div>

            <div className="export-descriptions">
              <div className="description-item">
                <strong>Raw Data:</strong> All participant responses, inquiries, and analysis data
              </div>
              <div className="description-item">
                <strong>Synthesis Report:</strong> Comprehensive summary of all dialogue rounds
              </div>
              <div className="description-item">
                <strong>Proposal:</strong> AI-generated proposal document based on dialogue outcomes
              </div>
              <div className="description-item">
                <strong>Agreement:</strong> Community agreement based on consensus points
              </div>
              <div className="description-item">
                <strong>Roadmap:</strong> Implementation plan with actions and timelines
              </div>
            </div>

            <div className="modal-actions">
              <button 
                className="btn btn-secondary" 
                onClick={() => setShowExportModal(false)}
                disabled={isExporting}
              >
                Cancel
              </button>
              <button 
                className="btn btn-success" 
                onClick={handleExport}
                disabled={isExporting}
              >
                {isExporting ? 'Generating Export...' : 'Download Export'}
              </button>
            </div>
          </div>
        </div>
      )}

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
          ) : analysis && analysis.analysis ? (
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
    </div>
  );
};

export default EventDetails; 