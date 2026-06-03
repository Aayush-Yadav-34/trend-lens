import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTrends, useTopics } from '../hooks/useTrends';
import FilterBar from '../components/FilterBar';
import TrendChart from '../components/TrendChart';
import TopicBubble from '../components/TopicBubble';
import SentimentBar from '../components/SentimentBar';
import TrendCard from '../components/TrendCard';

/* ---------- Skeleton Loader ---------- */
function SkeletonCard() {
  return (
    <div className="glass-card p-5 space-y-3">
      <div className="skeleton h-4 w-20 rounded" />
      <div className="skeleton h-4 w-full rounded" />
      <div className="skeleton h-3 w-2/3 rounded" />
    </div>
  );
}

function SkeletonChart() {
  return <div className="glass-card skeleton h-[340px] rounded-2xl" />;
}

function SkeletonStat() {
  return (
    <div className="stat-card">
      <div className="skeleton h-3 w-24 rounded" />
      <div className="skeleton h-8 w-16 rounded" />
    </div>
  );
}

/* ---------- Stat Card ---------- */
function StatCard({ label, value, icon, color }) {
  return (
    <div className="stat-card animate-slide-up">
      <div className="flex items-center gap-2">
        <span className={`text-lg ${color}`}>{icon}</span>
        <span className="text-xs font-semibold text-surface-500 uppercase tracking-wider">
          {label}
        </span>
      </div>
      <p className="text-3xl font-bold text-surface-100 tabular-nums">
        {value}
      </p>
    </div>
  );
}

/* ---------- Dashboard Page ---------- */
function Dashboard() {
  const [source, setSource] = useState('all');
  const [hours, setHours] = useState(24);
  const navigate = useNavigate();

  const { data: posts, error: postsError, isLoading: postsLoading } = useTrends(source, hours);
  const { data: topics, error: topicsError, isLoading: topicsLoading } = useTopics(hours);

  const isLoading = postsLoading || topicsLoading;
  const error = postsError || topicsError;

  // Compute stats
  const totalPosts = posts?.length ?? 0;
  const avgSentiment = posts?.length
    ? (posts.reduce((sum, p) => sum + (p.sentiment ?? 0), 0) / posts.length).toFixed(2)
    : '—';
  const topicCount = topics?.length ?? 0;

  const handleTopicClick = (topicId) => {
    navigate(`/topic/${topicId}`);
  };

  return (
    <div className="space-y-6">
      {/* Filter Bar */}
      <FilterBar source={source} setSource={setSource} hours={hours} setHours={setHours} />

      {/* Error Banner */}
      {error && (
        <div className="error-banner animate-fade-in" id="dashboard-error">
          <svg className="w-5 h-5 text-rose-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <p className="text-sm">{error.message || 'Failed to load data. Please try again.'}</p>
        </div>
      )}

      {/* Stat Cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <SkeletonStat />
          <SkeletonStat />
          <SkeletonStat />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="Total Posts" value={totalPosts} icon="📊" color="text-brand-400" />
          <StatCard label="Avg Sentiment" value={avgSentiment} icon="💬" color="text-emerald-400" />
          <StatCard label="Topics Found" value={topicCount} icon="🧩" color="text-amber-400" />
        </div>
      )}

      {/* Trend Chart */}
      {isLoading ? (
        <SkeletonChart />
      ) : (
        <TrendChart posts={posts || []} />
      )}

      {/* Topic Bubble + Sentiment Bar — side by side */}
      {isLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3">
            <SkeletonChart />
          </div>
          <div className="lg:col-span-2">
            <SkeletonChart />
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3">
            <TopicBubble topics={topics || []} onTopicClick={handleTopicClick} />
          </div>
          <div className="lg:col-span-2">
            <SentimentBar topics={topics || []} />
          </div>
        </div>
      )}

      {/* Trend Cards Grid */}
      <div>
        <h2 className="text-sm font-semibold text-surface-300 uppercase tracking-wider mb-4">
          Top Posts
        </h2>
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(posts || []).slice(0, 20).map((post) => (
              <TrendCard key={post.id} post={post} />
            ))}
            {(!posts || posts.length === 0) && (
              <div className="col-span-2 glass-card p-8 text-center">
                <p className="text-surface-500">No posts found for the selected filters.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
