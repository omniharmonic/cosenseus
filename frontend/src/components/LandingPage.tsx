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
          <h1 className="gradient-text">Welcome to cosense.us</h1>
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
      
      {/* Function Cards Section */}
      <section className="features-section">
        <div className="container">
          <h2 className="section-title gradient-text">Platform Features</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3>Session-Based Identity</h3>
              <p>Simple two-path system: create a new session with your name or resume with a session code. No complex accounts required.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">💬</div>
              <h3>Interactive Dialogue Rounds</h3>
              <p>Guided participation through multiple rounds of AI-moderated conversation. Admins control the pace and review AI-generated prompts.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3>Advanced AI Analysis</h3>
              <p>Local Ollama-powered analysis that transforms natural language responses into structured insights, consensus detection, and perspective synthesis.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Data Visualization Suite</h3>
              <p>Interactive visualizations including cluster maps, sentiment timelines, word clouds, and consensus graphs to understand collective perspectives.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>Local-First Privacy</h3>
              <p>All processing happens locally with Ollama AI models. Your data stays on your device with complete privacy and control.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">📈</div>
              <h3>Dynamic Event Management</h3>
              <p>Create custom events with flexible inquiry design, participant management, and real-time response collection and analysis.</p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Use Cases Section */}
      <section className="use-cases-section">
        <div className="container">
          <h2 className="section-title gradient-text">Perfect For</h2>
          <div className="use-cases-grid">
            <div className="use-case-card">
              <h3>🏛️ Civic Events</h3>
              <p>Candidate meet-and-greets, community planning initiatives, and neighborhood policy feedback collection.</p>
            </div>
            
            <div className="use-case-card">
              <h3>👥 Small Groups</h3>
              <p>Consensus building, team decision-making, and collaborative problem-solving sessions.</p>
            </div>
            
            <div className="use-case-card">
              <h3>🎓 Educational</h3>
              <p>Civic engagement exercises, classroom discussions, and participatory learning experiences.</p>
            </div>
            
            <div className="use-case-card">
              <h3>🏢 Organizations</h3>
              <p>Stakeholder feedback, strategic planning, and organizational change management.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage; 