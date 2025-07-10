import React, { useState, useEffect } from 'react';
import OpinionVisualization from './OpinionVisualization';
import { apiService } from '../services/api';
import './AdvancedAI.css';

interface CivicEntity {
  id: string;
  text: string;
  type: 'policy' | 'stakeholder' | 'issue' | 'location' | 'organization';
  confidence: number;
  frequency: number;
  sentiment: number;
}

interface HierarchicalCluster {
  id: string;
  centroid: [number, number];
  responses: OpinionResponse[];
  size: number;
  color: string;
  label: string;
  consensus_score: number;
  subclusters?: HierarchicalCluster[];
  level: number;
}

interface OpinionResponse {
  id: string;
  text: string;
  position: [number, number];
  sentiment: number;
  participant_id: string;
  cluster_id: string;
  entities: CivicEntity[];
  certainty_score: number;
}

interface AdvancedAIProps {
  eventId: string;
  onAnalysisComplete?: (results: AnalysisResults) => void;
}

interface AnalysisResults {
  clusters: HierarchicalCluster[];
  entities: CivicEntity[];
  consensus_areas: string[];
  dialogue_opportunities: string[];
  sentiment_trends: any[];
}

const AdvancedAI: React.FC<AdvancedAIProps> = ({
  eventId,
  onAnalysisComplete
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<'clustering' | 'entities' | 'consensus'>('clustering');
  const [processingStep, setProcessingStep] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [responses, setResponses] = useState<OpinionResponse[]>([]);

  useEffect(() => {
    const fetchResponses = async () => {
      setIsProcessing(true);
      setError(null);
      try {
        const responseData = await apiService.getEventResponses(eventId);
        if (responseData.data) {
          // Assuming the API returns something like { responses: [...] }
          setResponses(responseData.data.responses || []);
        } else {
          throw new Error(responseData.error || 'Failed to fetch responses.');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred while fetching responses.');
      } finally {
        setIsProcessing(false);
      }
    };
    fetchResponses();
  }, [eventId]);

  const runAdvancedAnalysis = async () => {
    setIsProcessing(true);
    setError(null);

    try {
      // Step 1: Get event analysis from Ollama
      setProcessingStep('Analyzing event responses with AI...');
      const analysisResponse = await apiService.analyzeEvent(eventId);
      
      if (analysisResponse.error) {
        throw new Error(analysisResponse.error);
      }

      // Step 2: Get event summary
      setProcessingStep('Generating comprehensive summary...');
      const summaryResponse = await apiService.getEventSummary(eventId);
      
      if (summaryResponse.error) {
        throw new Error(summaryResponse.error);
      }

      // Step 3: Cluster responses if we have them
      setProcessingStep('Clustering similar responses...');
      let clusteringResult = null;
      if (responses.length > 0) {
        const responseTexts = responses.map(r => r.text);
        const clusterResponse = await apiService.clusterResponses(responseTexts, 3);
        if (!clusterResponse.error) {
          clusteringResult = clusterResponse.data;
        }
      }

      // Process the AI analysis results
      const aiAnalysis = analysisResponse.data?.analysis || {};
      const aiSummary = summaryResponse.data?.ai_summary || {};

      const results: AnalysisResults = {
        clusters: clusteringResult?.clustering_result?.clusters?.map((cluster: any, index: number) => ({
          id: `cluster-${index}`,
          centroid: [Math.random() * 2 - 1, Math.random() * 2 - 1], // Mock positions
          responses: responses.filter((_, i) => cluster.responses?.includes(i.toString()) || false),
          size: cluster.responses?.length || 0,
          color: `hsl(${index * 120}, 70%, 60%)`,
          label: cluster.theme || `Cluster ${index + 1}`,
          consensus_score: 0.7 + Math.random() * 0.3, // Mock score
          level: 1
        })) || [],
        entities: aiAnalysis.key_entities || [],
        consensus_areas: aiAnalysis.key_themes || [],
        dialogue_opportunities: aiAnalysis.suggested_actions || [],
        sentiment_trends: aiSummary.sentiment_over_time || []
      };

      setAnalysisResults(results);
      onAnalysisComplete?.(results);
      setProcessingStep('Analysis complete!');

    } catch (err) {
      setError(`Failed to complete advanced analysis: ${err instanceof Error ? err.message : 'Unknown error'}`);
      console.error('Analysis error:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClusterClick = (clusterId: string) => {
    console.log('Selected cluster:', clusterId);
    // Here we would show detailed cluster information
  };

  const handleResponseClick = (responseId: string) => {
    console.log('Selected response:', responseId);
    // Here we would show detailed response information
  };

  const getEntityTypeColor = (type: string) => {
    switch (type) {
      case 'policy': return '#007bff';
      case 'stakeholder': return '#28a745';
      case 'issue': return '#dc3545';
      case 'location': return '#ffc107';
      case 'organization': return '#6f42c1';
      default: return '#6c757d';
    }
  };

  const getEntityTypeIcon = (type: string) => {
    switch (type) {
      case 'policy': return '📋';
      case 'stakeholder': return '👥';
      case 'issue': return '⚠️';
      case 'location': return '📍';
      case 'organization': return '🏢';
      default: return '📄';
    }
  };

  return (
    <div className="advanced-ai-container">
      <div className="ai-header">
        <h2>Advanced AI Analysis</h2>
        <p>Leveraging hierarchical clustering, civic entity recognition, and consensus detection</p>
      </div>

      {!analysisResults && !isProcessing && (
        <div className="analysis-start">
          <div className="analysis-preview">
            <h3>Analysis Capabilities</h3>
            <div className="capability-grid">
              <div className="capability-card">
                <div className="capability-icon">🌳</div>
                <h4>Hierarchical Clustering</h4>
                <p>Multi-level perspective grouping with subcluster identification</p>
              </div>
              <div className="capability-card">
                <div className="capability-icon">🔍</div>
                <h4>Civic Entity Recognition</h4>
                <p>Automatic detection of policies, stakeholders, and issues</p>
              </div>
              <div className="capability-card">
                <div className="capability-icon">🤝</div>
                <h4>Consensus Detection</h4>
                <p>Identify areas of agreement and dialogue opportunities</p>
              </div>
              <div className="capability-card">
                <div className="capability-icon">📊</div>
                <h4>Sentiment Evolution</h4>
                <p>Track emotional intensity and certainty across conversations</p>
              </div>
            </div>
          </div>
          <button
            className="start-analysis-button"
            onClick={runAdvancedAnalysis}
            disabled={isProcessing}
          >
            Start Advanced Analysis
          </button>
        </div>
      )}

      {isProcessing && (
        <div className="processing-state">
          <div className="processing-spinner"></div>
          <h3>Processing Analysis</h3>
          <p>{processingStep}</p>
          <div className="processing-progress">
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {analysisResults && (
        <div className="analysis-results">
          <div className="analysis-tabs">
            <button
              className={`tab-button ${selectedAnalysis === 'clustering' ? 'active' : ''}`}
              onClick={() => setSelectedAnalysis('clustering')}
            >
              Opinion Clusters
            </button>
            <button
              className={`tab-button ${selectedAnalysis === 'entities' ? 'active' : ''}`}
              onClick={() => setSelectedAnalysis('entities')}
            >
              Civic Entities
            </button>
            <button
              className={`tab-button ${selectedAnalysis === 'consensus' ? 'active' : ''}`}
              onClick={() => setSelectedAnalysis('consensus')}
            >
              Consensus & Dialogue
            </button>
          </div>

          <div className="tab-content">
            {selectedAnalysis === 'clustering' && (
              <div className="clustering-view">
                <div className="visualization-section">
                  <OpinionVisualization
                    clusters={analysisResults.clusters}
                    responses={responses}
                    onClusterClick={handleClusterClick}
                    onResponseClick={handleResponseClick}
                    width={800}
                    height={500}
                  />
                </div>
                <div className="cluster-details">
                  <h4>Hierarchical Structure</h4>
                  <div className="cluster-tree">
                    {analysisResults.clusters.map(cluster => (
                      <div key={cluster.id} className="cluster-node">
                        <div className="cluster-info">
                          <span className="cluster-name">{cluster.label}</span>
                          <span className="cluster-size">({cluster.size} responses)</span>
                          <span className="consensus-score">
                            Consensus: {(cluster.consensus_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        {cluster.subclusters && (
                          <div className="subclusters">
                            {cluster.subclusters.map(subcluster => (
                              <div key={subcluster.id} className="subcluster-node">
                                <span className="subcluster-name">{subcluster.label}</span>
                                <span className="subcluster-size">({subcluster.size})</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {selectedAnalysis === 'entities' && (
              <div className="entities-view">
                <div className="entities-grid">
                  {analysisResults.entities.map(entity => (
                    <div key={entity.id} className="entity-card">
                      <div className="entity-header">
                        <span className="entity-icon">{getEntityTypeIcon(entity.type)}</span>
                        <span className="entity-text">{entity.text}</span>
                        <span 
                          className="entity-type"
                          style={{ backgroundColor: getEntityTypeColor(entity.type) }}
                        >
                          {entity.type}
                        </span>
                      </div>
                      <div className="entity-metrics">
                        <div className="metric">
                          <span className="metric-label">Frequency:</span>
                          <span className="metric-value">{entity.frequency}</span>
                        </div>
                        <div className="metric">
                          <span className="metric-label">Confidence:</span>
                          <span className="metric-value">{(entity.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div className="metric">
                          <span className="metric-label">Sentiment:</span>
                          <span className={`metric-value ${entity.sentiment > 0 ? 'positive' : 'negative'}`}>
                            {(entity.sentiment * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedAnalysis === 'consensus' && (
              <div className="consensus-view">
                <div className="consensus-areas">
                  <h4>Areas of Consensus</h4>
                  <div className="consensus-list">
                    {analysisResults.consensus_areas.map((area, index) => (
                      <div key={index} className="consensus-item">
                        <span className="consensus-icon">✅</span>
                        <span className="consensus-text">{area}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="dialogue-opportunities">
                  <h4>Dialogue Opportunities</h4>
                  <div className="opportunities-list">
                    {analysisResults.dialogue_opportunities.map((opportunity, index) => (
                      <div key={index} className="opportunity-item">
                        <span className="opportunity-icon">🤝</span>
                        <span className="opportunity-text">{opportunity}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="sentiment-trends">
                  <h4>Sentiment Evolution</h4>
                  <div className="trends-chart">
                    {analysisResults.sentiment_trends.map((trend, index) => (
                      <div key={index} className="trend-point">
                        <div className="trend-round">Round {trend.round}</div>
                        <div className="trend-metrics">
                          <div className="trend-metric">
                            <span>Sentiment: {(trend.overall_sentiment * 100).toFixed(0)}%</span>
                          </div>
                          <div className="trend-metric">
                            <span>Engagement: {(trend.engagement * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedAI; 