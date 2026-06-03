import { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';

function sentimentColor(sentiment) {
  if (sentiment > 0.05) return '#34d399';   // emerald-400
  if (sentiment < -0.05) return '#fb7185';  // rose-400
  return '#94a3b8';                          // slate-400
}

function TopicBubble({ topics, onTopicClick }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);

  const hierarchyData = useMemo(() => {
    if (!topics || topics.length === 0) return null;

    return {
      name: 'topics',
      children: topics.map((t) => ({
        name: t.label || 'Unknown',
        value: Math.max(t.post_count || 1, 1),
        sentiment: t.avg_sentiment || 0,
        id: t.id,
        post_count: t.post_count,
        top_keywords: t.top_keywords || [],
      })),
    };
  }, [topics]);

  useEffect(() => {
    if (!hierarchyData || !svgRef.current || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = 400;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    svg.attr('viewBox', `0 0 ${width} ${height}`);

    // Create pack layout
    const root = d3.hierarchy(hierarchyData)
      .sum((d) => d.value)
      .sort((a, b) => (b.value || 0) - (a.value || 0));

    const pack = d3.pack()
      .size([width, height])
      .padding(6);

    pack(root);

    // Draw bubbles
    const nodes = svg.append('g')
      .selectAll('g')
      .data(root.leaves())
      .join('g')
      .attr('transform', (d) => `translate(${d.x},${d.y})`)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        if (onTopicClick && d.data.id) {
          onTopicClick(d.data.id);
        }
      });

    // Background circle
    nodes.append('circle')
      .attr('r', 0)
      .attr('fill', (d) => sentimentColor(d.data.sentiment))
      .attr('fill-opacity', 0.15)
      .attr('stroke', (d) => sentimentColor(d.data.sentiment))
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.5)
      .transition()
      .duration(600)
      .ease(d3.easeCubicOut)
      .attr('r', (d) => d.r);

    // Hover effects
    nodes.on('mouseenter', function (event, d) {
      d3.select(this).select('circle')
        .transition()
        .duration(200)
        .attr('fill-opacity', 0.3)
        .attr('stroke-opacity', 0.9)
        .attr('stroke-width', 2);
    }).on('mouseleave', function () {
      d3.select(this).select('circle')
        .transition()
        .duration(200)
        .attr('fill-opacity', 0.15)
        .attr('stroke-opacity', 0.5)
        .attr('stroke-width', 1.5);
    });

    // Labels (only show if radius > 30)
    nodes.filter((d) => d.r > 30)
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.3em')
      .attr('fill', '#f1f5f9')
      .attr('font-size', (d) => Math.min(d.r / 3.5, 13))
      .attr('font-weight', '600')
      .attr('opacity', 0)
      .text((d) => {
        const label = d.data.name;
        return label.length > 16 ? label.slice(0, 14) + '…' : label;
      })
      .transition()
      .delay(400)
      .duration(400)
      .attr('opacity', 1);

    // Post count below label
    nodes.filter((d) => d.r > 30)
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.1em')
      .attr('fill', '#94a3b8')
      .attr('font-size', (d) => Math.min(d.r / 4.5, 11))
      .attr('opacity', 0)
      .text((d) => `${d.data.post_count} posts`)
      .transition()
      .delay(500)
      .duration(400)
      .attr('opacity', 1);

  }, [hierarchyData, onTopicClick]);

  if (!topics || topics.length === 0) {
    return (
      <div className="glass-card p-6 flex items-center justify-center h-[400px]">
        <p className="text-surface-500 text-sm">No topics available</p>
      </div>
    );
  }

  return (
    <div className="glass-card p-6 animate-fade-in" ref={containerRef}>
      <h2 className="text-sm font-semibold text-surface-300 uppercase tracking-wider mb-4">
        Topic Clusters
      </h2>
      <svg ref={svgRef} width="100%" height={400} />
    </div>
  );
}

export default TopicBubble;
