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
    return <div>Loading Opinion Map...</div>;
  }

  if (error) {
    return <div className="error-message">Error: {error}</div>;
  }

  if (!analysisData || !analysisData.analysis_results || !analysisData.analysis_results.users) {
    return <div>No analysis data available for this round.</div>;
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
    const currentTrace = acc[clusterIndex] as { x: (string | number | Date)[]; y: (string | number | Date)[]; text: string; };
    if(currentTrace.x && currentTrace.y && currentTrace.text) {
      (currentTrace.x as (string|number|Date)[]).push(user.x);
      (currentTrace.y as (string|number|Date)[]).push(user.y);
      (currentTrace.text as string) += user.response + '<br>';
    }
    return acc;
  }, []);

  return (
    <div className="opinion-cluster-map">
      <h3>Opinion Cluster Map</h3>
      <Plot
        data={plotData}
        layout={{
          title: 'Participant Opinion Clusters',
          xaxis: { title: 'Principal Component 1' },
          yaxis: { title: 'Principal Component 2' },
          hovermode: 'closest'
        }}
        config={{ responsive: true }}
      />
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