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
        if (respRes.error || !respRes.data || !Array.isArray(respRes.data)) {
          setError(respRes.error || 'No responses found');
          setLoading(false);
          return;
        }
        const responses = respRes.data.map((r: any) => r.content);
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

  if (loading) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>🎯 Response Cluster Map</h3>
        </div>
        <div className="loading-state">
          <div className="loading-spinner small"></div>
          <p>Loading cluster map...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>🎯 Response Cluster Map</h3>
        </div>
        <div className="error-state">
          <p>⚠️ Failed to load cluster map</p>
          <p className="error-text">{error}</p>
        </div>
      </div>
    );
  }
  
  if (!clusterData || !Array.isArray(clusterData.clusters) || clusterData.clusters.length === 0) {
    return (
      <div className="visualization-container">
        <div className="card-header">
          <h3>🎯 Response Cluster Map</h3>
        </div>
        <div className="empty-state">
          <p>No cluster data available yet.</p>
          <p>Response clusters will appear as participants submit responses.</p>
        </div>
      </div>
    );
  }

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
    <div className="visualization-container">
      <div className="card-header">
        <h3>🎯 Response Cluster Map</h3>
      </div>
      <div className="visualization-content">
        <Plot
          data={traces}
          layout={{
            autosize: true,
            margin: { l: 50, r: 50, t: 50, b: 100 },
            title: 'Clusters of Participant Responses',
            xaxis: { title: 'Dimension 1', tickfont: { color: '#FFFFFF' }, titlefont: { color: '#FFFFFF' } },
            yaxis: { title: 'Dimension 2', tickfont: { color: '#FFFFFF' }, titlefont: { color: '#FFFFFF' } },
            legend: { 
              orientation: 'h',
              x: 0.5,
              xanchor: 'center',
              y: -0.2,
              font: { color: '#FFFFFF' }
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

export default ResponseClusterMap; 