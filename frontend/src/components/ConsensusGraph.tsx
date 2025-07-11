import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { apiService } from '../services/api';

interface ConsensusGraphProps {
  eventId: string;
}

interface ConsensusCluster {
  cluster_label: string;
  responses: string[];
  agreement_score: number;
}

const ConsensusGraph: React.FC<ConsensusGraphProps> = ({ eventId }) => {
  const [clusters, setClusters] = useState<ConsensusCluster[]>([]);
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchConsensus = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiService.getConsensusGraph(eventId);
        if (res.error) {
          setError(res.error);
          setLoading(false);
          return;
        }
        setClusters(res.data?.consensus_clusters || []);
        setSummary(res.data?.summary || '');
      } catch (err) {
        setError('Failed to load consensus graph');
      } finally {
        setLoading(false);
      }
    };
    fetchConsensus();
  }, [eventId]);

  if (loading) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>📈 Consensus Graph</h3>
        </div>
        <div className="loading-state">
          <div className="loading-spinner small"></div>
          <p>Loading consensus graph...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>📈 Consensus Graph</h3>
        </div>
        <div className="error-state">
          <p>⚠️ Failed to load consensus graph</p>
          <p className="error-text">{error}</p>
        </div>
      </div>
    );
  }
  
  if (!clusters || clusters.length === 0) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>📈 Consensus Graph</h3>
        </div>
        <div className="empty-state">
          <p>No consensus data available yet.</p>
          <p>Consensus analysis will appear as participants submit responses.</p>
        </div>
      </div>
    );
  }

  const x = clusters.map(c => c.cluster_label);
  const y = clusters.map(c => c.agreement_score);
  const text = clusters.map(c => `${c.responses.length} responses`);

  return (
    <div className="visualization-container">
      <div className="card-header">
        <h3>📈 Consensus Graph</h3>
      </div>
      <div className="visualization-content">
        <Plot
          data={[{
            x,
            y,
            text,
            type: 'bar',
            marker: { color: '#4a90e2' },
          }]}
          layout={{
            autosize: true,
            margin: { l: 50, r: 50, t: 50, b: 100 },
            title: 'Agreement by Cluster',
            xaxis: { title: 'Cluster', tickfont: { color: '#FFFFFF' }, titlefont: { color: '#FFFFFF' } },
            yaxis: { title: 'Agreement Score', range: [0, 1], tickfont: { color: '#FFFFFF' }, titlefont: { color: '#FFFFFF' } },
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
        {summary && (
          <div style={{ 
            marginTop: '12px', 
            fontStyle: 'italic', 
            color: '#8E8E93',
            padding: '0 16px',
            textAlign: 'center'
          }}>
            {summary}
          </div>
        )}
      </div>
    </div>
  );
};

export default ConsensusGraph; 