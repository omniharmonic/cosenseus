import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './DialogueModeration.css';
import LoadingSpinner from './common/LoadingSpinner';
import { useNotification } from './common/NotificationProvider';

interface Prompt {
  title: string;
  content: string;
  regenerated?: boolean;
  parameters?: {
    creativity_level: string;
    tone: string;
    length: string;
    focus_areas?: string[];
  };
}

interface SynthesisReview {
  id: string;
  event_id: string;
  round_number: number;
  status: string;
  summary: string;
  next_round_prompts: Prompt[];
  created_at: string;
  updated_at: string | null;
}

interface DialogueModerationProps {
  eventId: string;
  roundNumber: number;
  onApprovalSuccess: () => void;
}

interface RegenerateParams {
  creativity_level: 'conservative' | 'moderate' | 'creative';
  tone: 'analytical' | 'engaging' | 'challenging';
  length: 'brief' | 'standard' | 'detailed';
  focus_areas: string[];
}

const DialogueModeration: React.FC<DialogueModerationProps> = ({ eventId, roundNumber, onApprovalSuccess }) => {
  const [synthesis, setSynthesis] = useState<SynthesisReview | null>(null);
  const [editablePrompts, setEditablePrompts] = useState<Prompt[]>([]);
  const [editingPromptIndex, setEditingPromptIndex] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isApproving, setIsApproving] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenerateParams, setRegenerateParams] = useState<RegenerateParams>({
    creativity_level: 'moderate',
    tone: 'analytical',
    length: 'standard',
    focus_areas: []
  });
  const [focusAreaInput, setFocusAreaInput] = useState('');
  const { showNotification } = useNotification();

  useEffect(() => {
    const fetchSynthesis = async () => {
      setIsLoading(true);
      try {
        const response = await (apiService as any).getSynthesisForReview(eventId, roundNumber);
        if (response.data) {
          const synthesisReview = response.data;
          setSynthesis(synthesisReview);
          // Ensure prompts are always in the correct format
          const prompts = (synthesisReview.next_round_prompts || []).map((p: any) => 
            typeof p === 'string' ? { title: 'Generated Prompt', content: p } : p
          );
          setEditablePrompts(prompts);
          setError(null);
        } else {
          const errorMsg = (typeof response.error === 'object' ? JSON.stringify(response.error) : response.error) || `Failed to fetch synthesis for round ${roundNumber}.`;
          setError(errorMsg);
          showNotification(errorMsg, 'error');
        }
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || err.message || 'An unexpected error occurred.';
        setError(errorMessage);
        showNotification(errorMessage, 'error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSynthesis();
  }, [eventId, roundNumber, showNotification]);

  const handlePromptChange = (index: number, value: string) => {
    const newPrompts = [...editablePrompts];
    newPrompts[index] = { ...newPrompts[index], content: value };
    setEditablePrompts(newPrompts);
  };

  const handleRegeneratePrompts = async () => {
    if (!synthesis) return;
    setIsRegenerating(true);
    
    try {
      const sessionCode = localStorage.getItem('cosenseus_session_code');
      const response = await fetch(`/api/v1/ai/synthesis-review/${synthesis.id}/regenerate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Code': sessionCode || ''
        },
        body: JSON.stringify(regenerateParams)
      });

      if (response.ok) {
        const updatedSynthesis = await response.json();
        setSynthesis(updatedSynthesis);
        
        // Update editable prompts with regenerated ones
        const newPrompts = (updatedSynthesis.next_round_prompts || []).map((p: any) => 
          typeof p === 'string' ? { title: 'Generated Prompt', content: p } : p
        );
        setEditablePrompts(newPrompts);
        
        showNotification('Prompts regenerated successfully!', 'success');
        setShowRegenerateModal(false);
        setError(null);
      } else {
        const errorData = await response.json();
        const errorMsg = errorData.detail || 'Failed to regenerate prompts';
        setError(errorMsg);
        showNotification(errorMsg, 'error');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to regenerate prompts';
      setError(errorMessage);
      showNotification(errorMessage, 'error');
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleRegenerateIndividualPrompt = async (promptIndex: number) => {
    if (!synthesis) return;
    setIsRegenerating(true);
    
    try {
      const sessionCode = localStorage.getItem('cosenseus_session_code');
      const response = await fetch(`/api/v1/ai/synthesis-review/${synthesis.id}/regenerate-prompt/${promptIndex}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Code': sessionCode || ''
        },
        body: JSON.stringify(regenerateParams)
      });

      if (response.ok) {
        const result = await response.json();
        
        // Update the specific prompt in the editable prompts
        const newPrompts = [...editablePrompts];
        const newPrompt = result.new_prompt;
        newPrompts[promptIndex] = {
          ...newPrompts[promptIndex],
          title: newPrompt.title || newPrompts[promptIndex].title,
          content: newPrompt.content || newPrompt,
          regenerated: true
        };
        setEditablePrompts(newPrompts);
        
        // Update synthesis with the new prompts list
        setSynthesis({
          ...synthesis,
          next_round_prompts: result.updated_prompts
        });
        
        const successMessage = result.warning 
          ? `Prompt ${promptIndex + 1} regenerated (template used due to AI unavailability)`
          : `Prompt ${promptIndex + 1} regenerated successfully!`;
        
        showNotification(successMessage, result.warning ? 'info' : 'success');
        setError(null);
      } else {
        const errorData = await response.json();
        const errorMsg = errorData.detail || 'Failed to regenerate prompt';
        setError(errorMsg);
        showNotification(errorMsg, 'error');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to regenerate prompt';
      setError(errorMessage);
      showNotification(errorMessage, 'error');
    } finally {
      setIsRegenerating(false);
    }
  };

  const addFocusArea = () => {
    if (focusAreaInput.trim() && !regenerateParams.focus_areas.includes(focusAreaInput.trim())) {
      setRegenerateParams(prev => ({
        ...prev,
        focus_areas: [...prev.focus_areas, focusAreaInput.trim()]
      }));
      setFocusAreaInput('');
    }
  };

  const removeFocusArea = (area: string) => {
    setRegenerateParams(prev => ({
      ...prev,
      focus_areas: prev.focus_areas.filter(a => a !== area)
    }));
  };

  const handleUpdateSynthesis = async (): Promise<boolean> => {
    if (!synthesis) return false;
    setIsSaving(true);
    try {
      const response = await (apiService as any).updateSynthesis(synthesis.id, { next_round_prompts: editablePrompts });
      if (response.data) {
        showNotification('Draft saved successfully!', 'success');
        setEditingPromptIndex(null);
        setError(null);
        return true;
      } else {
        const errorMsg = (typeof response.error === 'object' ? JSON.stringify(response.error) : response.error) || 'Failed to save draft.';
        setError(errorMsg);
        showNotification(errorMsg, 'error');
        return false;
      }
    } catch (err: any) {
        let errorMessage = err.message || 'An unexpected error occurred.';
        if (err.response?.data?.detail) {
            errorMessage = typeof err.response.data.detail === 'object' 
                ? JSON.stringify(err.response.data.detail) 
                : err.response.data.detail;
        }
        setError(errorMessage);
        showNotification(errorMessage, 'error');
        return false;
    } finally {
      setIsSaving(false);
    }
  };

  const handleApproveSynthesis = async () => {
    if (!synthesis) return;
    setIsApproving(true);
    
    const updateSuccess = await handleUpdateSynthesis();
    if (!updateSuccess) {
      setIsApproving(false);
      showNotification('Could not approve because saving failed. Please resolve errors and try again.', 'error');
      return;
    }

    try {
      const response = await (apiService as any).approveSynthesis(synthesis.id);
      if (response.data) {
        showNotification('Synthesis approved! Starting next round.', 'success');
        setTimeout(onApprovalSuccess, 2000);
      } else {
        const errorMsg = (typeof response.error === 'object' ? JSON.stringify(response.error) : response.error) || 'Failed to approve synthesis.';
        setError(errorMsg);
        showNotification(errorMsg, 'error');
      }
    } catch (err: any) {
        let errorMessage = err.message || 'An unexpected error occurred.';
        if (err.response?.data?.detail) {
            errorMessage = typeof err.response.data.detail === 'object' 
                ? JSON.stringify(err.response.data.detail) 
                : err.response.data.detail;
        }
        setError(errorMessage);
        showNotification(errorMessage, 'error');
    } finally {
      setIsApproving(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error && !synthesis) {
    return <div className="dialogue-moderation-error">Error: {error}</div>;
  }

  if (!synthesis) {
    return <div className="dialogue-moderation-container">No synthesis available for review for this round.</div>;
  }

  return (
    <div className="dialogue-moderation-container">
      <h3>Review AI Synthesis for Round {synthesis.round_number}</h3>
      <p><strong>Summary of Previous Round:</strong></p>
      <div className="synthesis-summary">
        {synthesis.summary}
      </div>

      <div className="prompts-header">
        <h4>Proposed Prompts for Next Round:</h4>
        <button 
          className="btn btn-secondary regenerate-all-btn"
          onClick={() => setShowRegenerateModal(true)}
          disabled={isRegenerating || isSaving}
        >
          🔄 Regenerate All Prompts
        </button>
      </div>
      
      <p>Review, edit, and approve the AI-generated prompts for the next round of dialogue.</p>
      {error && <div className="dialogue-moderation-error" style={{ marginBottom: '1rem' }}>{error}</div>}
      
      <div className="prompt-list">
        {editablePrompts.map((prompt, index) => (
          <div key={index} className="prompt-item">
            <div className="prompt-header">
              <h5 className="prompt-title">{prompt.title}</h5>
              {prompt.regenerated && (
                <span className="regenerated-badge">🔄 Regenerated</span>
              )}
            </div>
            {editingPromptIndex === index ? (
              <textarea
                value={prompt.content}
                onChange={(e) => handlePromptChange(index, e.target.value)}
                className="prompt-textarea"
                rows={4}
              />
            ) : (
              <p className="prompt-text">{prompt.content}</p>
            )}
            {prompt.parameters && (
              <div className="regeneration-params">
                <small>
                  Generated with: {prompt.parameters.creativity_level} creativity, 
                  {prompt.parameters.tone} tone, {prompt.parameters.length} length
                  {prompt.parameters.focus_areas && prompt.parameters.focus_areas.length > 0 && 
                    `, focusing on: ${prompt.parameters.focus_areas.join(', ')}`
                  }
                </small>
              </div>
            )}
            <div className="prompt-actions">
              {editingPromptIndex === index ? (
                <button onClick={handleUpdateSynthesis} className="btn btn-primary prompt-button save" disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
              ) : (
                <>
                  <button onClick={() => setEditingPromptIndex(index)} className="btn btn-secondary prompt-button edit">
                    Edit
                  </button>
                  <button 
                    onClick={() => handleRegenerateIndividualPrompt(index)} 
                    className="btn btn-tertiary prompt-button regenerate-individual"
                    disabled={isRegenerating || isSaving}
                    title="Regenerate this prompt only"
                  >
                    🔄
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="moderation-actions">
        <button onClick={handleApproveSynthesis} disabled={isApproving || editingPromptIndex !== null} className="btn btn-primary approve-button">
          {isApproving ? 'Approving...' : `Approve & Start Round ${synthesis.round_number + 1}`}
        </button>
        {editingPromptIndex !== null && <p className="save-prompt-notice">Please save your changes before approving.</p>}
      </div>

      {/* Regenerate Modal */}
      {showRegenerateModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Regenerate Prompts</h3>
            <p>Adjust parameters to regenerate all prompts with different characteristics:</p>
            
            <div className="param-group">
              <label>Creativity Level:</label>
              <select 
                value={regenerateParams.creativity_level}
                onChange={(e) => setRegenerateParams(prev => ({...prev, creativity_level: e.target.value as any}))}
              >
                <option value="conservative">Conservative (focused, predictable)</option>
                <option value="moderate">Moderate (balanced)</option>
                <option value="creative">Creative (innovative, varied)</option>
              </select>
            </div>

            <div className="param-group">
              <label>Tone:</label>
              <select 
                value={regenerateParams.tone}
                onChange={(e) => setRegenerateParams(prev => ({...prev, tone: e.target.value as any}))}
              >
                <option value="analytical">Analytical (thoughtful, examining)</option>
                <option value="engaging">Engaging (conversational, welcoming)</option>
                <option value="challenging">Challenging (probing, deeper thinking)</option>
              </select>
            </div>

            <div className="param-group">
              <label>Length:</label>
              <select 
                value={regenerateParams.length}
                onChange={(e) => setRegenerateParams(prev => ({...prev, length: e.target.value as any}))}
              >
                <option value="brief">Brief (concise questions)</option>
                <option value="standard">Standard (moderate detail)</option>
                <option value="detailed">Detailed (comprehensive context)</option>
              </select>
            </div>

            <div className="param-group">
              <label>Focus Areas (optional):</label>
              <div className="focus-areas-input">
                <input
                  type="text"
                  value={focusAreaInput}
                  onChange={(e) => setFocusAreaInput(e.target.value)}
                  placeholder="Add a focus area..."
                  onKeyPress={(e) => e.key === 'Enter' && addFocusArea()}
                />
                <button type="button" onClick={addFocusArea} className="btn btn-secondary btn-sm">
                  Add
                </button>
              </div>
              <div className="focus-areas-list">
                {regenerateParams.focus_areas.map((area, index) => (
                  <span key={index} className="focus-area-tag">
                    {area}
                    <button onClick={() => removeFocusArea(area)}>×</button>
                  </span>
                ))}
              </div>
            </div>

            <div className="modal-actions">
              <button 
                className="btn btn-secondary" 
                onClick={() => setShowRegenerateModal(false)}
                disabled={isRegenerating}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleRegeneratePrompts}
                disabled={isRegenerating}
              >
                {isRegenerating ? 'Regenerating...' : 'Regenerate Prompts'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DialogueModeration; 