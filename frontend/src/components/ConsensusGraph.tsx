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

  if (loading) return <div>Loading consensus graph...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;
  if (!clusters || clusters.length === 0) return <div>No consensus data found.</div>;

  const x = clusters.map(c => c.cluster_label);
  const y = clusters.map(c => c.agreement_score);
  const text = clusters.map(c => `${c.responses.length} responses`);

  return (
    <div style={{ width: '100%', minHeight: 200, textAlign: 'center', padding: 16 }}>
      <h3>Consensus Graph</h3>
      <Plot
        data={[{
          x,
          y,
          text,
          type: 'bar',
          marker: { color: '#4a90e2' },
        }]}
        layout={{
          width: 600,
          height: 400,
          title: 'Agreement by Cluster',
          xaxis: { title: 'Cluster' },
          yaxis: { title: 'Agreement Score', range: [0, 1] },
        }}
      />
      {summary && <div style={{ marginTop: 12, fontStyle: 'italic', color: '#555' }}>{summary}</div>}
    </div>
  );
};

export default ConsensusGraph; 