import React from 'react';
import './Logo.css';

interface LogoProps {
  size?: 'small' | 'medium' | 'large';
  animated?: boolean;
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 'medium', animated = true, className = '' }) => {
  const sizeMap = {
    small: 60,
    medium: 120,
    large: 200
  };

  const logoSize = sizeMap[size];

  return (
    <div className={`census-logo ${size} ${className}`} style={{ width: logoSize, height: logoSize }}>
      <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="gradientStroke" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#40e0d0', stopOpacity: 1 }} />
            <stop offset="50%" style={{ stopColor: '#48cae4', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#0077b6', stopOpacity: 1 }} />
          </linearGradient>
          
          <radialGradient id="nodeGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" style={{ stopColor: '#40e0d0', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#0077b6', stopOpacity: 0.8 }} />
          </radialGradient>
          
          <linearGradient id="connectionGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#40e0d0', stopOpacity: 0.8 }} />
            <stop offset="100%" style={{ stopColor: '#48cae4', stopOpacity: 0.4 }} />
          </linearGradient>
          
          <radialGradient id="coreGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" style={{ stopColor: '#ffffff', stopOpacity: 0.9 }} />
            <stop offset="50%" style={{ stopColor: '#40e0d0', stopOpacity: 0.8 }} />
            <stop offset="100%" style={{ stopColor: '#0077b6', stopOpacity: 0.6 }} />
          </radialGradient>
        </defs>
        
        {/* Outer convergence circle */}
        <circle 
          className={`convergence-circle ${animated ? 'animated' : ''}`}
          cx="100" 
          cy="100" 
          r="85" 
          fill="none"
          stroke="url(#gradientStroke)"
          strokeWidth="3"
        />
        
        {/* Dialogue nodes around the circle */}
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="100" cy="30" r="8" />
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="150" cy="50" r="7" />
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="170" cy="100" r="8" />
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="150" cy="150" r="7" />
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="100" cy="170" r="8" />
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="50" cy="150" r="7" />
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="30" cy="100" r="8" />
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="50" cy="50" r="7" />
        
        {/* Connection lines from center circle edge to outer nodes */}
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="100" y1="75" x2="100" y2="30" />
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="118" y1="82" x2="150" y2="50" />
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="125" y1="100" x2="170" y2="100" />
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="118" y1="118" x2="150" y2="150" />
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="100" y1="125" x2="100" y2="170" />
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="82" y1="118" x2="50" y2="150" />
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="75" y1="100" x2="30" y2="100" />
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="82" y1="82" x2="50" y2="50" />
        
        {/* Central AI core */}
        <circle 
          className={`ai-core ${animated ? 'animated' : ''}`}
          cx="100" 
          cy="100" 
          r="25" 
          fill="url(#coreGradient)"
        />
        
        {/* Inner neural network pattern */}
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="100" cy="100" r="3" opacity="0.9" />
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="88" cy="95" r="2" opacity="0.7" />
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="112" cy="105" r="2" opacity="0.7" />
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="95" cy="110" r="2" opacity="0.7" />
        <circle className={`dialogue-node ${animated ? 'animated' : ''}`} cx="105" cy="90" r="2" opacity="0.7" />
        
        {/* Neural connections */}
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="100" y1="100" x2="88" y2="95" opacity="0.5" />
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="100" y1="100" x2="112" y2="105" opacity="0.5" />
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="100" y1="100" x2="95" y2="110" opacity="0.5" />
        <line className={`connection-line ${animated ? 'animated' : ''}`} x1="100" y1="100" x2="105" y2="90" opacity="0.5" />
      </svg>
    </div>
  );
};

export default Logo; 