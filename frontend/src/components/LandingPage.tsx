import React from 'react';
import Logo from './Logo';
import './LandingPage.css';

interface LandingPageProps {
  onGetStarted: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted }) => {
  return (
    <div className="landing-page">
      <header className="landing-page-header">
        <nav>
          <button onClick={onGetStarted} className="nav-link-button">Sign In</button>
        </nav>
      </header>
      <main className="hero-section">
        <div className="hero-content">
          <h1 className="gradient-text">Welcome to CoSenseus</h1>
          <p>
            An AI-enabled dialogue tool for building consensus through generative conversation.
          </p>
          <div className="cta-buttons">
            <button onClick={onGetStarted} className="btn btn-primary">
              Get Started
            </button>
          </div>
        </div>
        <div className="hero-logo">
          <Logo size="large" animated={true} />
        </div>
      </main>
    </div>
  );
};

export default LandingPage; 