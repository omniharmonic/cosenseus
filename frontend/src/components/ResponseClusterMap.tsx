import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { apiService } from '../services/api';
import type Plotly from 'plotly.js-dist';

interface ResponseClusterMapProps {
  eventId: string;
}

const ResponseClusterMap: React.FC<ResponseClusterMapProps> = ({ eventId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clusterData, setClusterData] = useState<any>(null);

  useEffect(() => {
    const fetchAndCluster = async () => {
      setLoading(true);
      setError(null);
      try {
        // 1. Fetch all responses for the event
        const respRes = await apiService.getEventResponses(eventId);
        if (respRes.error || !respRes.data || !respRes.data.responses) {
          setError(respRes.error || 'No responses found');
          setLoading(false);
          return;
        }
        const responses = respRes.data.responses.map((r: any) => r.content);
        if (responses.length === 0) {
          setError('No responses to cluster');
          setLoading(false);
          return;
        }
        // 2. Send responses to /ai/cluster-responses
        const clusterRes = await apiService.clusterResponses(responses, 3);
        if (clusterRes.error || !clusterRes.data || !clusterRes.data.clustering_result) {
          setError(clusterRes.error || 'Clustering failed');
          setLoading(false);
          return;
        }
        setClusterData(clusterRes.data.clustering_result);
      } catch (err) {
        setError('Failed to load cluster data');
      } finally {
        setLoading(false);
      }
    };
    fetchAndCluster();
  }, [eventId]);

  if (loading) return <div>Loading cluster map...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;
  if (!clusterData || !Array.isArray(clusterData.clusters) || clusterData.clusters.length === 0) return <div>No cluster data available.</div>;

  // Prepare data for Plotly
  const traces = (clusterData.clusters || []).map((cluster: any, idx: number) => ({
    x: (cluster.points || []).map((p: any) => p.x),
    y: (cluster.points || []).map((p: any) => p.y),
    text: (cluster.points || []).map((p: any) => p.text),
    mode: 'markers',
    type: 'scatter',
    name: `Cluster ${idx + 1}`,
    marker: { size: 12 },
    hoverinfo: 'text',
  }));

  return (
    <div>
      <h3>Response Cluster Map</h3>
      <Plot
        data={traces}
        layout={{
          width: 600,
          height: 400,
          title: 'Clusters of Participant Responses',
          xaxis: { title: 'Dimension 1' },
          yaxis: { title: 'Dimension 2' },
          legend: { orientation: 'h' },
        }}
      />
    </div>
  );
};

export default ResponseClusterMap; 