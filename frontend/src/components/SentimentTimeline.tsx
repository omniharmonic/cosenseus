import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { apiService } from '../services/api';

interface SentimentTimelineProps {
  eventId: string;
}

const sentimentToY = (sentiment: string): number => {
  switch (sentiment) {
    case 'positive': return 1;
    case 'neutral': return 0;
    case 'negative': return -1;
    default: return 0;
  }
};

const SentimentTimeline: React.FC<SentimentTimelineProps> = ({ eventId }) => {
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTimeline = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiService.getSentimentTimeline(eventId);
        if (res.error) {
          setError(res.error);
          setLoading(false);
          return;
        }
        setTimeline(res.data?.timeline || []);
      } catch (err) {
        setError('Failed to load sentiment timeline');
      } finally {
        setLoading(false);
      }
    };
    fetchTimeline();
  }, [eventId]);

  if (loading) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>📊 Sentiment Timeline</h3>
        </div>
        <div className="loading-state">
          <div className="loading-spinner small"></div>
          <p>Loading sentiment timeline...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>📊 Sentiment Timeline</h3>
        </div>
        <div className="error-state">
          <p>⚠️ Failed to load sentiment timeline</p>
          <p className="error-text">{error}</p>
        </div>
      </div>
    );
  }
  
  if (!timeline || timeline.length === 0) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>📊 Sentiment Timeline</h3>
        </div>
        <div className="empty-state">
          <p>No sentiment data available yet.</p>
          <p>Sentiment analysis will appear as participants submit responses.</p>
        </div>
      </div>
    );
  }

  // Prepare data for Plotly
  const x = timeline.map((point) => point.created_at);
  const y = timeline.map((point) => sentimentToY(point.sentiment));
  const text = timeline.map((point) => `Sentiment: ${point.sentiment}\nConfidence: ${point.confidence}\n${point.summary}`);

  return (
    <div className="visualization-container">
      <div className="card-header">
        <h3>📊 Sentiment Timeline</h3>
      </div>
      <div className="visualization-content">
        <Plot
        data={[{
          x,
          y,
          text,
          mode: 'lines+markers',
          type: 'scatter',
          marker: { size: 10, color: '#4a90e2' },
          line: { shape: 'linear', color: '#4a90e2' },
        }]}
        layout={{
          autosize: true,
          margin: { l: 50, r: 50, t: 50, b: 50 },
          title: 'Sentiment Over Time',
          xaxis: { title: 'Time', tickfont: { color: '#FFFFFF' }, titlefont: { color: '#FFFFFF' } },
          yaxis: {
            title: 'Sentiment',
            tickvals: [-1, 0, 1],
            ticktext: ['Negative', 'Neutral', 'Positive'],
            tickfont: { color: '#FFFFFF' },
            titlefont: { color: '#FFFFFF' }
          },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#FFFFFF' },
          titlefont: { color: '#FFFFFF' }
        }}
        config={{ 
          responsive: true,
          displayModeBar: false,
          staticPlot: false
        }}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
      </div>
    </div>
  );
};

export default SentimentTimeline; 