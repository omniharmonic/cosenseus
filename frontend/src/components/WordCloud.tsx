import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';

interface WordCloudProps {
  eventId: string;
}

interface Keyword {
  word: string;
  frequency: number;
}

const getFontSize = (frequency: number, min: number, max: number) => {
  // Scale font size between 14px and 48px
  if (max === min) return 24;
  return 14 + ((frequency - min) / (max - min)) * (48 - 14);
};

const WordCloud: React.FC<WordCloudProps> = ({ eventId }) => {
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchKeywords = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiService.getWordCloud(eventId);
        if (res.error) {
          setError(res.error);
          setLoading(false);
          return;
        }
        setKeywords(res.data?.keywords || []);
      } catch (err) {
        setError('Failed to load word cloud');
      } finally {
        setLoading(false);
      }
    };
    fetchKeywords();
  }, [eventId]);

  if (loading) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>☁️ Word Cloud</h3>
        </div>
        <div className="loading-state">
          <div className="loading-spinner small"></div>
          <p>Loading word cloud...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>☁️ Word Cloud</h3>
        </div>
        <div className="error-state">
          <p>⚠️ Failed to load word cloud</p>
          <p className="error-text">{error}</p>
        </div>
      </div>
    );
  }
  
  if (!keywords || keywords.length === 0) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>☁️ Word Cloud</h3>
        </div>
        <div className="empty-state">
          <p>No keywords available yet.</p>
          <p>Word analysis will appear as participants submit responses.</p>
        </div>
      </div>
    );
  }

  const minFreq = Math.min(...keywords.map(k => k.frequency));
  const maxFreq = Math.max(...keywords.map(k => k.frequency));

  return (
    <div className="visualization-container">
      <div className="card-header">
        <h3>☁️ Word Cloud</h3>
      </div>
      <div className="visualization-content">
        <div style={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          justifyContent: 'center', 
          gap: '8px',
          padding: '16px',
          minHeight: '200px',
          alignItems: 'center'
        }}>
          {keywords.map((k, i) => (
            <span
              key={i}
              style={{
                fontSize: getFontSize(k.frequency, minFreq, maxFreq),
                fontWeight: 600,
                color: '#ffffff',
                margin: 4,
                lineHeight: 1.2,
                transition: 'transform 0.2s ease',
                cursor: 'default'
              }}
              title={`Frequency: ${k.frequency}`}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.1)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
            >
              {k.word}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WordCloud; 