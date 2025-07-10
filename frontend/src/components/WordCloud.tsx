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

  if (loading) return <div>Loading word cloud...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;
  if (!keywords || keywords.length === 0) return <div>No keywords found.</div>;

  const minFreq = Math.min(...keywords.map(k => k.frequency));
  const maxFreq = Math.max(...keywords.map(k => k.frequency));

  return (
    <div style={{ width: '100%', minHeight: 200, textAlign: 'center', padding: 16 }}>
      <h3>Word Cloud</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 8 }}>
        {keywords.map((k, i) => (
          <span
            key={i}
            style={{
              fontSize: getFontSize(k.frequency, minFreq, maxFreq),
              fontWeight: 600,
              color: '#ffffff',
              margin: 4,
              lineHeight: 1.2,
            }}
            title={`Frequency: ${k.frequency}`}
          >
            {k.word}
          </span>
        ))}
      </div>
    </div>
  );
};

export default WordCloud; 