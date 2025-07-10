import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './DialogueModeration.css';
import LoadingSpinner from './common/LoadingSpinner';
import { useNotification } from './common/NotificationProvider';

interface Prompt {
  title: string;
  content: string;
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

const DialogueModeration: React.FC<DialogueModerationProps> = ({ eventId, roundNumber, onApprovalSuccess }) => {
  const [synthesis, setSynthesis] = useState<SynthesisReview | null>(null);
  const [editablePrompts, setEditablePrompts] = useState<Prompt[]>([]);
  const [editingPromptIndex, setEditingPromptIndex] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isApproving, setIsApproving] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
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

      <h4>Proposed Prompts for Next Round:</h4>
      <p>Review, edit, and approve the AI-generated prompts for the next round of dialogue.</p>
      {error && <div className="dialogue-moderation-error" style={{ marginBottom: '1rem' }}>{error}</div>}
      <div className="prompt-list">
        {editablePrompts.map((prompt, index) => (
          <div key={index} className="prompt-item">
            <h5 className="prompt-title">{prompt.title}</h5>
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
            <div className="prompt-actions">
              {editingPromptIndex === index ? (
                <button onClick={handleUpdateSynthesis} className="btn btn-primary prompt-button save" disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
              ) : (
                <button onClick={() => setEditingPromptIndex(index)} className="btn btn-secondary prompt-button edit">
                  Edit
                </button>
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
    </div>
  );
};

export default DialogueModeration; 