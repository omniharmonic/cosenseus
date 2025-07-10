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

  if (loading) return <div>Loading sentiment timeline...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;
  if (!timeline || timeline.length === 0) return <div>No sentiment data available.</div>;

  // Prepare data for Plotly
  const x = timeline.map((point) => point.created_at);
  const y = timeline.map((point) => sentimentToY(point.sentiment));
  const text = timeline.map((point) => `Sentiment: ${point.sentiment}\nConfidence: ${point.confidence}\n${point.summary}`);

  return (
    <div style={{ width: '100%', minHeight: 300, padding: 16 }}>
      <h3>Sentiment Timeline</h3>
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
          xaxis: { title: 'Time' },
          yaxis: {
            title: 'Sentiment',
            tickvals: [-1, 0, 1],
            ticktext: ['Negative', 'Neutral', 'Positive'],
          },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#F2F2F7' }
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
  );
};

export default SentimentTimeline; 