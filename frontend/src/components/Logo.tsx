import React from 'react';
import './Logo.css';

interface LogoProps {
  size?: 'small' | 'medium' | 'large';
  animated?: boolean;
  className?: string;
}

const CoSenseusLogo: React.FC<LogoProps> = ({ size = 'medium', animated = true, className = '' }) => {
  return (
    <div className={`cosenseus-logo ${size} ${className}`}>
      <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <defs>
          {/* Dark Royal Blue Gradient */}
          <linearGradient id="outer-circle-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#5C85D6', stopOpacity: 1 }} />
            <stop offset="50%" style={{ stopColor: '#2F58B8', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#1A294A', stopOpacity: 1 }} />
          </linearGradient>
          <linearGradient id="node-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#5C85D6', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#2F58B8', stopOpacity: 1 }} />
          </linearGradient>
          <radialGradient id="ai-core-gradient">
            <stop offset="0%" style={{ stopColor: '#5C85D6', stopOpacity: 0.8 }} />
            <stop offset="100%" style={{ stopColor: '#1A294A', stopOpacity: 1 }} />
          </radialGradient>
          <filter id="glow-effect" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Outer convergence circle */}
        <circle cx="100" cy="100" r="90" fill="none" stroke="url(#outer-circle-gradient)" strokeWidth="4" />

        {/* AI Core */}
        <circle cx="100" cy="100" r="30" fill="url(#ai-core-gradient)" filter="url(#glow-effect)" className="ai-core" />
        
        {/* Dialogue Nodes */}
        {[...Array(4)].map((_, i) => (
          <circle 
            key={i}
            cx={100 + 60 * Math.cos(i * Math.PI / 2)} 
            cy={100 + 60 * Math.sin(i * Math.PI / 2)} 
            r="10" 
            className="dialogue-node" 
          />
        ))}
      </svg>
    </div>
  );
};

export default CoSenseusLogo; 