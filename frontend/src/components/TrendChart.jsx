import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const SOURCE_COLORS = {
  reddit: '#f97316',
  hn: '#f59e0b',
  github: '#94a3b8',
};

function TrendChart({ posts }) {
  const chartData = useMemo(() => {
    if (!posts || posts.length === 0) return [];

    // Group posts into hourly buckets by fetched_at
    const buckets = {};

    posts.forEach((post) => {
      if (!post.fetched_at) return;
      const date = new Date(post.fetched_at);
      // Round to hour
      const hourKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:00`;

      if (!buckets[hourKey]) {
        buckets[hourKey] = { hour: hourKey, reddit: 0, hn: 0, github: 0 };
      }
      if (post.source in buckets[hourKey]) {
        buckets[hourKey][post.source] += 1;
      }
    });

    // Sort by hour and return
    return Object.values(buckets).sort((a, b) => a.hour.localeCompare(b.hour));
  }, [posts]);

  if (!chartData.length) {
    return (
      <div className="glass-card p-6 flex items-center justify-center h-[300px]">
        <p className="text-surface-500 text-sm">No data available for chart</p>
      </div>
    );
  }

  return (
    <div className="glass-card p-6 animate-fade-in">
      <h2 className="text-sm font-semibold text-surface-300 uppercase tracking-wider mb-4">
        Post Volume Over Time
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.5} />
          <XAxis
            dataKey="hour"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickFormatter={(value) => {
              const parts = value.split(' ');
              return parts[1] || value;
            }}
            axisLine={{ stroke: '#334155' }}
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '12px',
              color: '#f1f5f9',
              fontSize: '12px',
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }}
          />
          <Line
            type="monotone"
            dataKey="reddit"
            stroke={SOURCE_COLORS.reddit}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: SOURCE_COLORS.reddit }}
            name="Reddit"
          />
          <Line
            type="monotone"
            dataKey="hn"
            stroke={SOURCE_COLORS.hn}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: SOURCE_COLORS.hn }}
            name="Hacker News"
          />
          <Line
            type="monotone"
            dataKey="github"
            stroke={SOURCE_COLORS.github}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: SOURCE_COLORS.github }}
            name="GitHub"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TrendChart;
