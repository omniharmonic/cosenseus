import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import './OpinionVisualization.css';

interface OpinionCluster {
  id: string;
  centroid: [number, number];
  responses: OpinionResponse[];
  size: number;
  color: string;
  label: string;
  consensus_score: number;
}

interface OpinionResponse {
  id: string;
  text: string;
  position: [number, number];
  sentiment: number;
  participant_id: string;
  cluster_id: string;
}

interface OpinionVisualizationProps {
  clusters: OpinionCluster[];
  responses: OpinionResponse[];
  onClusterClick?: (clusterId: string) => void;
  onResponseClick?: (responseId: string) => void;
  width?: number;
  height?: number;
  isInteractive?: boolean;
}

const OpinionVisualization: React.FC<OpinionVisualizationProps> = ({
  clusters,
  responses,
  onClusterClick,
  onResponseClick,
  width = 800,
  height = 600,
  isInteractive = true
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null);
  const [hoveredResponse, setHoveredResponse] = useState<string | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);

  useEffect(() => {
    if (!svgRef.current || clusters.length === 0) return;

    // Clear previous visualization
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current);
    const margin = { top: 40, right: 40, bottom: 40, left: 40 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    // Create chart group
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Set up scales
    const xScale = d3.scaleLinear()
      .domain([-1, 1])
      .range([0, chartWidth]);

    const yScale = d3.scaleLinear()
      .domain([-1, 1])
      .range([chartHeight, 0]);

    // Create zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.5, 5])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
        setZoomLevel(event.transform.k);
      });

    svg.call(zoom as any);

    // Add grid lines
    const gridG = g.append("g").attr("class", "grid");
    
    // Vertical grid lines
    gridG.selectAll("line.vertical")
      .data([-0.8, -0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8])
      .enter()
      .append("line")
      .attr("class", "vertical")
      .attr("x1", d => xScale(d))
      .attr("x2", d => xScale(d))
      .attr("y1", 0)
      .attr("y2", chartHeight)
      .attr("stroke", "#e0e0e0")
      .attr("stroke-width", 1)
      .attr("opacity", 0.5);

    // Horizontal grid lines
    gridG.selectAll("line.horizontal")
      .data([-0.8, -0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8])
      .enter()
      .append("line")
      .attr("class", "horizontal")
      .attr("x1", 0)
      .attr("x2", chartWidth)
      .attr("y1", d => yScale(d))
      .attr("y2", d => yScale(d))
      .attr("stroke", "#e0e0e0")
      .attr("stroke-width", 1)
      .attr("opacity", 0.5);

    // Add axis labels
    g.append("text")
      .attr("class", "axis-label")
      .attr("x", chartWidth / 2)
      .attr("y", chartHeight + 30)
      .attr("text-anchor", "middle")
      .text("Opinion Spectrum");

    g.append("text")
      .attr("class", "axis-label")
      .attr("transform", "rotate(-90)")
      .attr("x", -chartHeight / 2)
      .attr("y", -30)
      .attr("text-anchor", "middle")
      .text("Sentiment");

    // Draw clusters
    const clusterG = g.append("g").attr("class", "clusters");

    clusterG.selectAll("circle.cluster")
      .data(clusters)
      .enter()
      .append("circle")
      .attr("class", "cluster")
      .attr("cx", d => xScale(d.centroid[0]))
      .attr("cy", d => yScale(d.centroid[1]))
      .attr("r", d => Math.max(20, Math.sqrt(d.size) * 3))
      .attr("fill", d => d.color)
      .attr("stroke", "#333")
      .attr("stroke-width", 2)
      .attr("opacity", d => selectedCluster ? (d.id === selectedCluster ? 1 : 0.3) : 0.8)
      .style("cursor", isInteractive ? "pointer" : "default")
      .on("click", (event, d) => {
        if (isInteractive && onClusterClick) {
          setSelectedCluster(d.id);
          onClusterClick(d.id);
        }
      })
      .on("mouseenter", (event, d) => {
        if (isInteractive) {
          d3.select(event.currentTarget)
            .attr("stroke-width", 3)
            .attr("opacity", 1);
        }
      })
      .on("mouseleave", (event, d) => {
        if (isInteractive) {
          d3.select(event.currentTarget)
            .attr("stroke-width", 2)
            .attr("opacity", selectedCluster ? (d.id === selectedCluster ? 1 : 0.3) : 0.8);
        }
      });

    // Add cluster labels
    clusterG.selectAll("text.cluster-label")
      .data(clusters)
      .enter()
      .append("text")
      .attr("class", "cluster-label")
      .attr("x", d => xScale(d.centroid[0]))
      .attr("y", d => yScale(d.centroid[1]))
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .attr("fill", "#333")
      .text(d => d.label);

    // Add cluster size indicators
    clusterG.selectAll("text.cluster-size")
      .data(clusters)
      .enter()
      .append("text")
      .attr("class", "cluster-size")
      .attr("x", d => xScale(d.centroid[0]))
      .attr("y", d => yScale(d.centroid[1]) + 25)
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("fill", "#666")
      .text(d => `${d.size} responses`);

    // Draw individual responses
    const responseG = g.append("g").attr("class", "responses");

    responseG.selectAll("circle.response")
      .data(responses)
      .enter()
      .append("circle")
      .attr("class", "response")
      .attr("cx", d => xScale(d.position[0]))
      .attr("cy", d => yScale(d.position[1]))
      .attr("r", 4)
      .attr("fill", d => {
        const cluster = clusters.find(c => c.id === d.cluster_id);
        return cluster ? cluster.color : "#999";
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 1)
      .attr("opacity", d => {
        if (selectedCluster) {
          return d.cluster_id === selectedCluster ? 0.8 : 0.2;
        }
        return 0.6;
      })
      .style("cursor", isInteractive ? "pointer" : "default")
      .on("click", (event, d) => {
        const response = d as OpinionResponse;
        if (isInteractive && onResponseClick) {
          onResponseClick(response.id);
        }
      })
      .on("mouseenter", (event, d) => {
        const response = d as OpinionResponse;
        if (isInteractive) {
          setHoveredResponse(response.id);
          d3.select(event.currentTarget)
            .attr("r", 6)
            .attr("opacity", 1);
        }
      })
      .on("mouseleave", (event, d) => {
        const response = d as OpinionResponse;
        if (isInteractive) {
          setHoveredResponse(null);
          d3.select(event.currentTarget)
            .attr("r", 4)
            .attr("opacity", selectedCluster ? (response.cluster_id === selectedCluster ? 0.8 : 0.2) : 0.6);
        }
      });

    // Add tooltips for responses
    const tooltip = d3.select("body").append("div")
      .attr("class", "tooltip")
      .style("opacity", 0);

    responseG.selectAll("circle.response")
      .on("mouseenter", (event, d) => {
        const response = d as OpinionResponse;
        tooltip.transition()
          .duration(200)
          .style("opacity", 0.9);
        tooltip.html(`
          <div class="tooltip-content">
            <strong>Response:</strong><br/>
            ${response.text.substring(0, 100)}${response.text.length > 100 ? '...' : ''}<br/>
            <strong>Sentiment:</strong> ${(response.sentiment * 100).toFixed(1)}%
          </div>
        `)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseleave", () => {
        tooltip.transition()
          .duration(500)
          .style("opacity", 0);
      });

    // Add consensus areas
    const consensusG = g.append("g").attr("class", "consensus-areas");

    clusters.forEach(cluster => {
      if (cluster.consensus_score > 0.7) {
        consensusG.append("circle")
          .attr("class", "consensus-area")
          .attr("cx", xScale(cluster.centroid[0]))
          .attr("cy", yScale(cluster.centroid[1]))
          .attr("r", Math.max(30, Math.sqrt(cluster.size) * 4))
          .attr("fill", "none")
          .attr("stroke", "#28a745")
          .attr("stroke-width", 2)
          .attr("stroke-dasharray", "5,5")
          .attr("opacity", 0.6);
      }
    });

    // Add legend
    const legendG = g.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(${chartWidth - 150}, 20)`);

    legendG.append("text")
      .attr("class", "legend-title")
      .attr("x", 0)
      .attr("y", 0)
      .attr("font-weight", "bold")
      .text("Clusters");

    legendG.selectAll("rect.legend-item")
      .data(clusters)
      .enter()
      .append("rect")
      .attr("class", "legend-item")
      .attr("x", 0)
      .attr("y", (d, i) => 20 + i * 20)
      .attr("width", 12)
      .attr("height", 12)
      .attr("fill", d => d.color)
      .attr("stroke", "#333")
      .attr("stroke-width", 1);

    legendG.selectAll("text.legend-label")
      .data(clusters)
      .enter()
      .append("text")
      .attr("class", "legend-label")
      .attr("x", 20)
      .attr("y", (d, i) => 30 + i * 20)
      .attr("font-size", "11px")
      .text(d => `${d.label} (${d.size})`);

    // Cleanup function
    return () => {
      d3.select("body").selectAll(".tooltip").remove();
    };

  }, [clusters, responses, selectedCluster, width, height, isInteractive, onClusterClick, onResponseClick]);

  return (
    <div className="opinion-visualization">
      <div className="visualization-header">
        <h3>Opinion Landscape</h3>
        <div className="visualization-controls">
          <button
            className="btn btn-secondary control-button"
            onClick={() => setSelectedCluster(null)}
            disabled={!selectedCluster}
          >
            Show All Clusters
          </button>
          <span className="zoom-level">Zoom: {Math.round(zoomLevel * 100)}%</span>
        </div>
      </div>
      
      <div className="visualization-container">
        <svg
          ref={svgRef}
          width={width}
          height={height}
          className="opinion-chart"
        />
      </div>

      {selectedCluster && (
        <div className="cluster-details">
          <h4>Selected Cluster</h4>
          <p>
            {clusters.find(c => c.id === selectedCluster)?.label}
          </p>
        </div>
      )}
    </div>
  );
};

export default OpinionVisualization; 