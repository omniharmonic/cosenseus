import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { Data } from 'plotly.js';
import { apiService } from '../services/api';
import './OpinionClusterMap.css';

interface OpinionClusterMapProps {
  eventId: string;
  roundNumber: number;
}

interface AnalysisUser {
  user_id: string;
  response: string;
  x: number;
  y: number;
  cluster: number;
}

const OpinionClusterMap: React.FC<OpinionClusterMapProps> = ({ eventId, roundNumber }) => {
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        const res = await apiService.getPolisAnalysis(eventId, roundNumber);
        if (res.data) {
          setAnalysisData(res.data);
        } else {
          setError(res.error || 'Failed to fetch analysis data.');
        }
      } catch (err) {
        setError('An unexpected error occurred.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (eventId && roundNumber > 0) {
      fetchAnalysis();
    }
  }, [eventId, roundNumber]);

  if (loading) {
    return (
      <div className="opinion-cluster-map-container">
        <div className="ocm-header">
          <h3>Opinion Cluster Map</h3>
        </div>
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-color-secondary-dark)' }}>
          Loading Opinion Map...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="opinion-cluster-map-container">
        <div className="ocm-header">
          <h3>Opinion Cluster Map</h3>
        </div>
        <div className="ocm-error-message">
          <p>Unable to load opinion analysis</p>
          <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>{error}</p>
        </div>
      </div>
    );
  }

  if (!analysisData || !analysisData.analysis_results || !analysisData.analysis_results.users) {
    return (
      <div className="opinion-cluster-map-container">
        <div className="ocm-header">
          <h3>Opinion Cluster Map</h3>
        </div>
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-color-secondary-dark)' }}>
          No analysis data available for this round. Responses are needed to generate opinion clusters.
        </div>
      </div>
    );
  }

  const { statements, analysis_results } = analysisData;
  const { users } = analysis_results;

  // Prepare data for Plotly
  const plotData = users.reduce((acc: Partial<Data>[], user: AnalysisUser) => {
    const clusterIndex = user.cluster;
    if (!acc[clusterIndex]) {
      acc[clusterIndex] = {
        x: [],
        y: [],
        text: [],
        type: 'scatter',
        mode: 'markers',
        name: `Cluster ${clusterIndex + 1}`,
        marker: { size: 12 }
      };
    }
    // Type assertion to tell TypeScript that acc[clusterIndex] is now defined and has these properties
    const currentTrace = acc[clusterIndex] as { x: (string | number | Date)[]; y: (string | number | Date)[]; text: (string | number | Date)[]; };
    if(currentTrace.x && currentTrace.y && currentTrace.text) {
      (currentTrace.x as (string|number|Date)[]).push(user.x);
      (currentTrace.y as (string|number|Date)[]).push(user.y);
      (currentTrace.text as (string|number|Date)[]).push(user.response);
    }
    return acc;
  }, []);

  return (
    <div className="opinion-cluster-map-container">
      <div className="ocm-header">
        <h3>Opinion Cluster Map</h3>
      </div>
      <div className="plot-container">
        <Plot
          data={plotData}
          layout={{
            autosize: true,
            margin: { l: 50, r: 50, t: 50, b: 50 },
            title: 'Participant Opinion Clusters',
            xaxis: { title: 'Principal Component 1' },
            yaxis: { title: 'Principal Component 2' },
            hovermode: 'closest',
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
      <div className="statements-list">
        <h4>Key Statements</h4>
        <ol>
          {statements.map((stmt: string, index: number) => (
            <li key={index}>{stmt}</li>
          ))}
        </ol>
      </div>
    </div>
  );
};

export default OpinionClusterMap; 