import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './DialogueRounds.css';

interface Inquiry {
  id: string;
  question_text: string;
  description: string;
  response_type: string;
  is_required: boolean;
  order_index: number;
}

interface RoundAnalysis {
  round_number: number;
  summary: string;
  key_themes: string[];
  consensus_points: string[];
  dialogue_opportunities: string[];
  participant_count: number;
  created_at: string;
  analysis?: any;
  next_round_prompts?: Array<{ title: string; content: string }>; // Correctly typed
}

interface DialogueRoundsProps {
  eventId: string;
  onComplete: () => void;
  onBack: () => void;
  isAdmin?: boolean; // Simulate admin for now
}

const DialogueRounds: React.FC<DialogueRoundsProps> = ({ 
  eventId, 
  onComplete, 
  onBack,
  isAdmin = false,
}) => {
  const isParticipant = !isAdmin;
  const [currentRound, setCurrentRound] = useState(1);
  const [roundStatus, setRoundStatus] = useState<'waiting_for_responses' | 'in_analysis' | 'admin_review' | 'completed'>('waiting_for_responses');
  const [inquiries, setInquiries] = useState<Inquiry[]>([]);
  const [roundAnalyses, setRoundAnalyses] = useState<RoundAnalysis[]>([]);
  const [responses, setResponses] = useState<{[key: string]: string}>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [eventDetails, setEventDetails] = useState<any>(null);
  const [feedback, setFeedback] = useState<string>('');
  const [pollInterval, setPollInterval] = useState<any>(null);
  const [isWaitingForNextRound, setIsWaitingForNextRound] = useState(false);

  console.log(
    '[DialogueRounds Render] EventID:', eventId, 
    '| Status:', roundStatus, 
    '| Loading:', loading, 
    '| Error:', error, 
    '| Inquiries:', inquiries?.length
  );

  // Poll round state
  const fetchRoundState = async () => {
    try {
      console.log('[DialogueRounds fetchRoundState] Fetching state for event:', eventId);
      const res = await fetch(`/api/v1/events/${eventId}/round-state`);
      if (!res.ok) {
        throw new Error(`Round state fetch failed with status ${res.status}`);
      }
      const data = await res.json();
      console.log('[DialogueRounds fetchRoundState] API Response:', data);
      if (data && typeof data.current_round !== 'undefined') {
        setCurrentRound(data.current_round);
        // The backend uses 'waiting_for_responses' for the active/open state.
        setRoundStatus(data.status);
      }
    } catch (err) {
      console.error('[DialogueRounds fetchRoundState] Error:', err);
      setError('Failed to fetch round state.');
    }
  };

  useEffect(() => {
    // On mount, load from localStorage and then start polling
    const saved = localStorage.getItem(`census_dialogue_${eventId}`);
    if (saved) {
      const parsed = JSON.parse(saved);
      setCurrentRound(parsed.currentRound || 1);
      setResponses(parsed.responses || {});
    }
    
    fetchRoundState(); // Initial fetch
    const interval = setInterval(fetchRoundState, 3000); // Poll every 3 seconds
    
    return () => clearInterval(interval); // Cleanup on unmount
  }, [eventId]);


  const fetchEventData = async () => {
    if (!eventId) return;
    setLoading(true);
    console.log('[DialogueRounds fetchEventData] Fetching data for event:', eventId);
    try {
      // Fetch event details
      const eventResponse = await apiService.getEvent(eventId);
      console.log('[DialogueRounds fetchEventData] getEvent response:', eventResponse);
      if (eventResponse.error) {
        setError(eventResponse.error);
        return;
      }
      setEventDetails(eventResponse.data);

      // Fetch inquiries for the event
      const inquiriesResponse = await apiService.getEventInquiries(eventId, currentRound);
      console.log('[DialogueRounds fetchEventData] getEventInquiries response:', inquiriesResponse);
      if (inquiriesResponse.error) {
        setError(inquiriesResponse.error);
        setIsWaitingForNextRound(false);
        return;
      }
      
      if (currentRound > 1 && (!inquiriesResponse.data || inquiriesResponse.data.length === 0)) {
        setIsWaitingForNextRound(true);
        setInquiries([]);
      } else {
        setIsWaitingForNextRound(false);
        setInquiries(inquiriesResponse.data || []);
      }

      if (currentRound > 1) {
        const roundResultsResponse = await apiService.getEventRoundResults(eventId, currentRound - 1);
        console.log('[DialogueRounds fetchEventData] getEventRoundResults response:', roundResultsResponse);
        if (roundResultsResponse && roundResultsResponse.data) {
          setRoundAnalyses(roundResultsResponse.data as RoundAnalysis[]);
        } else {
          console.log('No round analyses found:', roundResultsResponse.error);
        }
      }

      setError(null);
    } catch (err) {
      console.error('[DialogueRounds fetchEventData] Error:', err);
      setError('Failed to load event data');
      console.error('Error fetching event data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResponseChange = (inquiryId: string, value: string) => {
    setResponses(prev => ({
      ...prev,
      [inquiryId]: value
    }));
  };

  const submitRoundResponses = async () => {
    if (Object.keys(responses).length > 0) {
      setSubmitting(true);
      try {
        const sessionCode = localStorage.getItem('census_session_code');
        if (!sessionCode) {
          setError('No active session. Please log in again.');
          setSubmitting(false);
          return;
        }

        const responsesToSubmit = Object.entries(responses).map(([inquiryId, responseText]) => ({
          inquiry_id: inquiryId,
          content: responseText,
          round_number: currentRound,
          is_anonymous: false,
        }));

        const result = await apiService.submitRoundResponses(responsesToSubmit);
        
        if (result.error) {
          setError(result.error);
          return;
        }
        setResponses({});
        setError(null);
      } catch (err) {
        setError('Failed to submit responses');
        console.error('Error submitting responses:', err);
      } finally {
        setSubmitting(false);
      }
    }
  };

  const analyzeRound = async () => {
    setAnalyzing(true);
    try {
      const analysisResponse = await apiService.analyzeEventRound(eventId, currentRound);
      if (analysisResponse.error) {
        setError(analysisResponse.error);
        return;
      }
      // Add the new round analysis
      const newAnalysis: RoundAnalysis = {
        round_number: currentRound,
        summary: analysisResponse.data.analysis?.summary || `Round ${currentRound} analysis`,
        key_themes: analysisResponse.data.analysis?.key_themes || [],
        consensus_points: analysisResponse.data.analysis?.consensus_points || [],
        dialogue_opportunities: analysisResponse.data.analysis?.dialogue_opportunities || [],
        participant_count: analysisResponse.data.response_count || 0,
        created_at: analysisResponse.data.timestamp || new Date().toISOString(),
        analysis: analysisResponse.data.analysis,
        next_round_prompts: analysisResponse.data.next_round_prompts || [] // Add next_round_prompts
      };
      setRoundAnalyses(prev => [...prev, newAnalysis]);
      setError(null);
    } catch (err) {
      setError('Error analyzing round');
      console.error('Error analyzing round:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const submitFeedback = async (inquiryId: string) => {
    if (!feedback.trim()) return;
    try {
      const feedbackResponse = await apiService.submitRoundResponses([{
        inquiry_id: inquiryId,
        content: feedback,
        is_anonymous: false,
        round_number: currentRound
      }]);
      if (feedbackResponse.error) {
        setError(feedbackResponse.error);
        return;
      }
      setFeedback('');
      alert('Feedback submitted successfully!');
    } catch (err) {
      setError('Error submitting feedback');
      console.error('Error submitting feedback:', err);
    }
  };

  const advanceRound = async () => {
    try {
      await fetch(`/api/v1/events/${eventId}/advance-round`, { method: 'POST' });
      await fetchRoundState();
      setResponses({});
      setFeedback('');
      setError(null);
    } catch (err) {
      setError('Error advancing round');
    }
  };

  useEffect(() => {
    fetchEventData();
  }, [eventId, currentRound]);

  // --- UX POLISH & JOURNEY REFACTOR START ---
  // 1. Persist round and responses in localStorage
  useEffect(() => {
    const dataToSave = JSON.stringify({
      currentRound,
      responses
    });
    localStorage.setItem(`census_dialogue_${eventId}`, dataToSave);
  }, [currentRound, responses, eventId]);

  // 2. Add banners/instructions for each step
  const getBanner = () => {
    if (roundStatus === 'waiting_for_responses') {
      return currentRound === 1
        ? 'Welcome! Please share your initial thoughts on these questions.'
        : 'Reflect on the group’s key themes and respond to the new prompts.';
    }
    if (roundStatus === 'in_analysis') {
      return 'Thank you! Your responses are in. Waiting for AI analysis and admin action...';
    }
    if (roundStatus === 'completed') {
      return 'Dialogue complete! Thank you for your participation.';
    }
    return '';
  };
  // 3. Highlight dialogue prompts in analysis
  const currentAnalysis = roundAnalyses.find(analysis => analysis.round_number === currentRound - 1);
  const isLastRound = currentRound === 3;
  // 4. Add a visual progress bar/stepper
  const renderProgress = () => (
    <div className="progress-indicator">
      {[1, 2, 3].map(round => (
        <div 
          key={round}
          className={`progress-step ${round <= currentRound ? 'active' : ''} ${round < currentRound ? 'completed' : ''}`}
        >
          {round < currentRound ? '✓' : round}
        </div>
      ))}
    </div>
  );
  // 5. Auto-transition from waiting to open/completed
  useEffect(() => {
    if (roundStatus === 'in_analysis') {
      const interval = setInterval(fetchRoundState, 2000);
      return () => clearInterval(interval);
    }
  }, [roundStatus]);
  // --- UX POLISH & JOURNEY REFACTOR END ---

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

  if (loading && inquiries.length === 0) {
    return (
      <div className="dialogue-rounds-container">
        <div className="loading-spinner"></div>
        <p>Loading dialogue...</p>
      </div>
    );
  }

  if (isWaitingForNextRound) {
    return (
      <div className="dialogue-rounds-container">
        <div className="loading-spinner"></div>
        <p>The next round is being prepared. Please wait...</p>
      </div>
    );
  }

  if (error || !eventDetails) {
    return (
      <div className="dialogue-rounds-container">
        <div className="error-state">
          <h3>Error Loading Dialogue</h3>
          <p>{typeof error === 'string' ? error : JSON.stringify(error, null, 2) || 'Event not found'}</p>
          <button className="btn btn-primary" onClick={onBack}>
            Back to Event Details
          </button>
        </div>
      </div>
    );
  }

  if (roundStatus === 'admin_review') {
    return (
      <div className="waiting-for-analysis">
          <h3>Round {currentRound} is complete.</h3>
          <p>The moderator is reviewing the results. The next round will begin shortly.</p>
          <div className="loading-spinner"></div>
      </div>
    );
  }

  // Participant view: show questions if round is open
  if (roundStatus === 'waiting_for_responses') {
    return (
      <div className="dialogue-rounds-container">
        <div className="rounds-header">
          <button className="btn btn-secondary btn-sm back-button" onClick={onBack}>
            ← Back to Event
          </button>
          <div className="rounds-progress">
            <h1>Dialogue Round {currentRound}</h1>
            {renderProgress()}
          </div>
        </div>
        <div className="dialogue-content">
          <div className="banner">
            <p>{getBanner()}</p>
          </div>
          
          {/* Show previous round analysis for context */}
          {currentRound > 1 && currentAnalysis && (
            <div className="analysis-dashboard">
              <h2>📊 Insights from Round {currentRound - 1}</h2>
              <div className="analysis-grid">
                <div className="analysis-card">
                  <h3>🎯 Key Themes</h3>
                  <ul>
                    {currentAnalysis.key_themes.map((theme, index) => (
                      <li key={index}>{theme}</li>
                    ))}
                  </ul>
                </div>
                <div className="analysis-card">
                  <h3>🤝 Areas of Agreement</h3>
                  <ul>
                    {currentAnalysis.consensus_points.map((point, index) => (
                      <li key={index}>{point}</li>
                    ))}
                  </ul>
                </div>
                <div className="analysis-card">
                  <h3>💡 Next Steps</h3>
                  <ul>
                    {currentAnalysis.dialogue_opportunities.map((opportunity, index) => (
                      <li key={index}>{opportunity}</li>
                    ))}
                  </ul>
                </div>
              </div>
              
              {/* Dialogue prompts for this round */}
              {currentAnalysis.next_round_prompts && currentAnalysis.next_round_prompts.length > 0 && (
                <div className="next-round-prompts">
                  <h3>🗣️ Focus Areas for This Round</h3>
                  <ul>
                    {currentAnalysis.next_round_prompts.map((prompt, idx) => (
                      <li key={idx} className="dialogue-prompt">
                        <strong>{prompt.title}:</strong> {prompt.content}
                      </li>
                    ))}
                  </ul>
                  <p className="prompt-instructions">Please consider these focus areas as you respond to help move the discussion toward consensus.</p>
                </div>
              )}
            </div>
          )}
          
          {/* Current round questions */}
          <div className="current-round-questions">
            <h2>Your Responses for Round {currentRound}</h2>
            <p className="round-instructions">
              {currentRound === 1 
                ? "Please share your initial thoughts on these questions. Be as detailed as you'd like."
                : "Based on the group's insights, please provide additional perspectives or respond to the emerging themes."
              }
            </p>
            <div className="questions-list">
              {inquiries.map((inquiry, index) => (
                <div key={inquiry.id} className="question-card">
                  <div className="question-header">
                    <span className="question-number">Q{index + 1}</span>
                    <h3>{inquiry.question_text}</h3>
                  </div>
                  <p className="question-content">{inquiry.description}</p>
                  <div className="response-input">
                    <textarea
                      value={responses[inquiry.id] || ''}
                      onChange={(e) => handleResponseChange(inquiry.id, e.target.value)}
                      placeholder="Share your thoughts here..."
                      rows={4}
                      className="response-textarea"
                      required={inquiry.is_required}
                    />
                    <div className="response-counter">
                      {responses[inquiry.id]?.length || 0} characters
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Action buttons */}
          <div className="rounds-footer">
            <div className="feedback-section">
              <textarea 
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Provide feedback on the analysis or suggest a direction for the next round..."
              />
              <button 
                className="btn btn-secondary"
                onClick={() => submitFeedback('feedback-inquiry-id')} // Replace with a real inquiry ID if available
                disabled={!feedback.trim()}
              >
                Submit Feedback
              </button>
            </div>

            <div className="rounds-actions">
              {isParticipant && roundStatus === 'waiting_for_responses' && (
                <>
                  <button
                    className="btn btn-secondary"
                    onClick={onBack}
                    disabled={submitting || analyzing}
                  >
                    Save & Exit
                  </button>
                  <button
                    className="btn btn-primary"
                    onClick={submitRoundResponses}
                    disabled={submitting || analyzing || !inquiries.every(inq => responses[inq.id]?.trim())}
                  >
                    {submitting ? 'Submitting...' : `Submit Round ${currentRound} Responses`}
                  </button>
                </>
              )}

              {isAdmin && (
                <>
                  <button className="btn btn-secondary" onClick={onBack}>
                    Back to Event
                  </button>
                  <button className="btn btn-primary" onClick={advanceRound} disabled={analyzing}>
                    {analyzing ? 'Analyzing...' : `End Round ${currentRound} & Analyze`}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Waiting for analysis/admin
  if (roundStatus === 'in_analysis') {
    return (
      <div className="dialogue-rounds-container">
        <div className="rounds-header">
          <button className="btn btn-secondary btn-sm back-button" onClick={onBack}>
            ← Back to Event
          </button>
          <div className="rounds-progress">
            <h1>Dialogue Round {currentRound}</h1>
            {renderProgress()}
          </div>
        </div>
        <div className="dialogue-content">
          <div className="banner">
            <p>{getBanner()}</p>
          </div>
          <div className="waiting-for-analysis">
            <h3>Round {currentRound} is in analysis.</h3>
            <p>The moderator is reviewing the results. The next round will begin shortly.</p>
            <div className="loading-spinner"></div>
          </div>
        </div>
      </div>
    );
  }

  // Dialogue has ended
  return (
    <div className="dialogue-rounds-container">
      <div className="rounds-header">
          <button className="btn btn-secondary btn-sm back-button" onClick={onBack}>
            ← Back to Event
          </button>
        <div className="rounds-progress">
          <h1>Dialogue Complete</h1>
          {renderProgress()}
        </div>
      </div>
      <div className="dialogue-content">
        <div className="banner">
          <p>{getBanner()}</p>
        </div>
        <div className="final-analysis">
          <h2>Final Analysis & Report</h2>
          <p>The dialogue has concluded. Here are the final insights from all rounds.</p>
          {/* You could map over all roundAnalyses here to show a full report */}
        </div>
        <div className="rounds-actions">
          <button className="btn btn-primary" onClick={onComplete}>
            Complete Dialogue & View Final Report
          </button>
        </div>
      </div>
    </div>
  );
};

export default DialogueRounds; 