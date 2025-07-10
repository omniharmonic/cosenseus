import React from 'react';
import './EmptyState.css';

interface EmptyStateProps {
  title: string;
  message: string;
  action?: {
    text: string;
    onClick: () => void;
  };
}

const EmptyState: React.FC<EmptyStateProps> = ({ title, message, action }) => {
  return (
    <div className="empty-state-container">
      <h3>{title}</h3>
      <p>{message}</p>
      {action && (
        <button className="btn-primary" onClick={action.onClick}>
          {action.text}
        </button>
      )}
    </div>
  );
};

export default EmptyState; 