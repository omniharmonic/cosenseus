import React from 'react';
import Logo from './Logo';
import './LandingPage.css';

interface LandingPageProps {
  onGetStarted: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted }) => {
  return (
    <div className="App landing-page">
      <header className="hero-section">
        <div className="hero-logo">
          <Logo size="large" animated={true} />
        </div>
        <h1>CENSUS</h1>
        <p className="tagline">AI-powered civic dialogue for real consensus</p>
        <div className="hero-cta">
          <button className="cta-button" onClick={onGetStarted}>Get Started</button>
          <button className="cta-button-secondary">Learn More</button>
        </div>
      </header>
      <section className="how-it-works">
        <h2>How It Works</h2>
        <ol className="steps-list">
          <li><strong>1. Create or Join an Event:</strong> Start a civic dialogue or participate in one.</li>
          <li><strong>2. Share Your Perspective:</strong> Respond to open-ended questions in your own words.</li>
          <li><strong>3. AI Synthesis:</strong> Census analyzes responses, surfaces consensus, and highlights opportunities for dialogue.</li>
          <li><strong>4. Move Toward Agreement:</strong> Engage in multi-round dialogue, guided by AI-powered prompts.</li>
          <li><strong>5. See Results:</strong> Explore interactive visualizations and share insights with your community.</li>
        </ol>
      </section>
      <section className="discover-events">
        <h2>Discover Events</h2>
        <p>Jump into a live event or explore recent civic dialogues.</p>
        <button className="cta-button" onClick={onGetStarted}>Browse Events</button>
      </section>
      <footer className="app-footer">
        <div className="footer-content">
          <span>&copy; {new Date().getFullYear()} Census. All rights reserved.</span>
          <span className="footer-links">
            <a href="#" target="_blank" rel="noopener noreferrer">Contact</a> | <a href="#" target="_blank" rel="noopener noreferrer">About</a>
          </span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage; 