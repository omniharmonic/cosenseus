import React, { useState } from 'react';
import Logo from './Logo';
import './SignIn.css';

interface SignInProps {
  onCreateSession: (displayName: string) => Promise<void>;
  onLogin: (sessionCode: string) => Promise<void>;
  onBack: () => void;
}

const SignIn: React.FC<SignInProps> = ({ onCreateSession, onLogin }) => {
  const [isReturningUser, setIsReturningUser] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [sessionCode, setSessionCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!displayName.trim()) return;
    setLoading(true);
    setError('');
    try {
      await onCreateSession(displayName.trim());
    } catch (err) {
      setError('Failed to create session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sessionCode.trim()) return;
    setLoading(true);
    setError('');
    try {
      await onLogin(sessionCode.trim());
    } catch (err) {
      setError('Invalid session code. Please check and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signin-container">
      <div className="signin-card">
        <div className="signin-header">
          <div className="logo-container">
            <Logo size="large" animated={true} />
          </div>
          <h1>CENSUS</h1>
          <p>AI-powered civic dialogue for real consensus</p>
        </div>

        <div className="signin-content">
          {error && <p className="error-message">{error}</p>}

          {!isReturningUser ? (
            <form className="form-container" onSubmit={handleCreateSession}>
              <h2>Create a New Session</h2>
              <p>Enter your name to begin. You'll receive a session code to return later.</p>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter your name"
                className="signin-field"
                aria-label="Display Name"
              />
              <button 
                type="submit"
                className="btn-primary" 
                disabled={!displayName.trim() || loading}
              >
                {loading ? 'Continuing...' : 'Continue'}
              </button>
              <button 
                type="button"
                className="btn-link"
                onClick={() => setIsReturningUser(true)}
              >
                Returning user? Sign in here.
              </button>
            </form>
          ) : (
            <form className="form-container" onSubmit={handleLogin}>
              <h2>Resume Session</h2>
              <p>Enter the session code you received previously.</p>
              <input
                type="text"
                value={sessionCode}
                onChange={(e) => setSessionCode(e.target.value)}
                placeholder="Enter your session code"
                className="signin-field"
                aria-label="Session Code"
              />
              <button 
                type="submit"
                className="btn-primary" 
                disabled={!sessionCode.trim() || loading}
              >
                {loading ? 'Signing In...' : 'Sign In'}
              </button>
              <button 
                type="button"
                className="btn-link"
                onClick={() => setIsReturningUser(false)}
              >
                Back to new user
              </button>
            </form>
          )}
        </div>

        <div className="signin-footer">
          <p>Your participation helps build better civic dialogue</p>
        </div>
      </div>
    </div>
  );
};

export default SignIn; 