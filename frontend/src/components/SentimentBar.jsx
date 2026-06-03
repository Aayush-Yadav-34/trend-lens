import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

function SentimentBar({ topics }) {
  const chartData = useMemo(() => {
    if (!topics || topics.length === 0) return [];

    return topics.map((topic) => ({
      label: topic.label
        ? topic.label.length > 12
          ? topic.label.slice(0, 12) + '…'
          : topic.label
        : 'Unknown',
      fullLabel: topic.label || 'Unknown',
      avg_sentiment: topic.avg_sentiment || 0,
    }));
  }, [topics]);

  if (!chartData.length) {
    return (
      <div className="glass-card p-6 flex items-center justify-center h-[250px]">
        <p className="text-surface-500 text-sm">No sentiment data available</p>
      </div>
    );
  }

  return (
    <div className="glass-card p-6 animate-fade-in">
      <h2 className="text-sm font-semibold text-surface-300 uppercase tracking-wider mb-4">
        Topic Sentiment
      </h2>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.5} vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
            angle={-25}
            textAnchor="end"
            height={50}
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
            domain={[-1, 1]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '12px',
              color: '#f1f5f9',
              fontSize: '12px',
            }}
            formatter={(value, _name, props) => [
              value.toFixed(2),
              props.payload.fullLabel,
            ]}
            labelFormatter={() => ''}
          />
          <Bar dataKey="avg_sentiment" radius={[6, 6, 0, 0]} maxBarSize={40}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.avg_sentiment >= 0 ? '#34d399' : '#fb7185'}
                fillOpacity={0.8}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default SentimentBar;
