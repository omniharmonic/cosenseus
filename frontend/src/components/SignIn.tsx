import React, { useState } from 'react';
import Logo from './Logo';
import './SignIn.css';

interface SignInProps {
  onCreateSession: (displayName: string) => Promise<void>;
  onLogin: (sessionCode: string) => Promise<void>;
  onBack: () => void;
}

const SignIn: React.FC<SignInProps> = ({ onCreateSession, onLogin, onBack }) => {
  const [userName, setUserName] = useState('');
  const [sessionCode, setSessionCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onBack();
    }
  };

  const onSessionCreate = async () => {
    if (!userName.trim()) {
      setError('Please enter your name.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await onCreateSession(userName.trim());
      // On success, App.tsx will handle closing the modal and navigation
    } catch (err) {
      setError('Failed to create session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const onSessionLogin = async () => {
    if (!sessionCode.trim()) {
      setError('Please enter a session code.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await onLogin(sessionCode.trim());
      // On success, App.tsx will handle closing the modal and navigation
    } catch (err) {
      setError('Invalid session code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sign-in-backdrop" onClick={handleBackdropClick}>
      <div className="sign-in-box">
        <button onClick={onBack} className="close-button" aria-label="Close">
          &times;
        </button>
        <div className="cosenseus-logo">
          <Logo size="medium" />
        </div>
        <h2 className="gradient-text">Join the Conversation</h2>
        <p className="tagline">Create a session or enter a code to join an existing one.</p>

        {error && <div className="error-message">{error}</div>}

        <div className="form-section">
          <div className="form-group">
            <label htmlFor="name">First-time user?</label>
            <input
              id="name"
              type="text"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              placeholder="Enter your name"
              disabled={loading}
            />
          </div>
          <button onClick={onSessionCreate} className="btn btn-primary" style={{ width: '100%', marginBottom: 'var(--spacing-unit-3)' }} disabled={loading}>
            {loading ? 'Creating...' : 'Create Session'}
          </button>
          
          <div className="form-group">
            <label htmlFor="sessionCode">Returning user?</label>
            <input
              id="sessionCode"
              type="text"
              value={sessionCode}
              onChange={(e) => setSessionCode(e.target.value)}
              placeholder="Enter session code"
              disabled={loading}
            />
          </div>
          <button onClick={onSessionLogin} className="btn btn-secondary" style={{ width: '100%' }} disabled={loading}>
            {loading ? 'Joining...' : 'Join with Code'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SignIn; 