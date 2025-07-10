import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './DialogueModeration.css';

interface DialogueModerationProps {
  eventId: string;
  roundNumber: number;
}

const DialogueModeration: React.FC<DialogueModerationProps> = ({ eventId, roundNumber }) => {
  const [synthesis, setSynthesis] = useState<any>(null);
  const [prompts, setPrompts] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isApproving, setIsApproving] = useState(false);

  const fetchSynthesis = async () => {
    setLoading(true);
    try {
      const response = await apiService.getSynthesisForReview(eventId, roundNumber);
      if (response.data) {
        setSynthesis(response.data);
        setPrompts(JSON.stringify(response.data.next_round_prompts, null, 2));
      } else {
        setError(response.error || 'Failed to load synthesis for review.');
      }
    } catch (err) {
      setError('An error occurred while fetching the synthesis for review.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSynthesis();
  }, [eventId, roundNumber]);

  const handleSaveChanges = async () => {
    setIsSaving(true);
    try {
      const parsedPrompts = JSON.parse(prompts);
      await apiService.updateSynthesis(synthesis.id, { next_round_prompts: parsedPrompts });
      alert('Changes saved successfully!');
    } catch (err) {
      alert('Failed to save changes. Please check if the JSON format is correct.');
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleApprove = async () => {
    setIsApproving(true);
    if (window.confirm('Are you sure you want to approve these prompts and start the next round? This action cannot be undone.')) {
      try {
        await apiService.approveSynthesis(synthesis.id);
        alert('Round approved! The next round has started.');
        // Optionally, trigger a refresh of the event details page
        window.location.reload();
      } catch (err) {
        alert('Failed to approve the round.');
        console.error(err);
      }
    }
    setIsApproving(false);
  };

  if (loading) {
    return <div>Loading moderation panel...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  if (!synthesis) {
    return <div>No synthesis available for review for this round.</div>;
  }

  return (
    <div className="dialogue-moderation-panel">
      <h3>Review & Approve Next Round Prompts</h3>
      <p>
        Here you can review the AI-generated prompts for the next round. You can edit the JSON directly below and save your changes. 
        Once you are satisfied, approve the prompts to start the next round of dialogue for all participants.
      </p>
      
      <div className="synthesis-content">
        <h4>AI Synthesis Summary</h4>
        <p>{synthesis.summary || synthesis.content}</p>
      </div>

      <div className="prompts-editor">
        <h4>Next Round Prompts (JSON)</h4>
        <textarea 
          value={prompts}
          onChange={(e) => setPrompts(e.target.value)}
          rows={15}
        />
      </div>

      <div className="moderation-actions">
        <button onClick={handleSaveChanges} disabled={isSaving || isApproving}>
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
        <button onClick={handleApprove} disabled={isSaving || isApproving} className="approve-button">
          {isApproving ? 'Approving...' : 'Approve & Start Next Round'}
        </button>
      </div>
    </div>
  );
};

export default DialogueModeration; 