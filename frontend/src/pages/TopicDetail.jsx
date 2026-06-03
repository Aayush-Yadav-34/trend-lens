import { useParams, useNavigate } from 'react-router-dom';
import { useTopicPosts, useTopics } from '../hooks/useTrends';
import TrendCard from '../components/TrendCard';

function TopicDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: posts, error: postsError, isLoading: postsLoading } = useTopicPosts(id);
  const { data: topics } = useTopics();

  // Find the current topic from the topics list
  const topic = topics?.find((t) => t.id === Number(id));

  const isLoading = postsLoading;
  const error = postsError;

  function getSentimentColor(sentiment) {
    if (sentiment > 0.05) return 'text-emerald-400';
    if (sentiment < -0.05) return 'text-rose-400';
    return 'text-surface-400';
  }

  function getSentimentLabel(sentiment) {
    if (sentiment > 0.05) return 'Positive';
    if (sentiment < -0.05) return 'Negative';
    return 'Neutral';
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back Button */}
      <button
        id="back-to-dashboard"
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-sm text-surface-400 hover:text-surface-200 transition-colors group"
      >
        <svg
          className="w-4 h-4 transition-transform group-hover:-translate-x-1"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Dashboard
      </button>

      {/* Topic Header */}
      {topic ? (
        <div className="glass-card p-6 space-y-4">
          <h1 className="text-2xl font-bold text-surface-100">
            {topic.label}
          </h1>

          {/* Stats Row */}
          <div className="flex flex-wrap items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-surface-500">Posts:</span>
              <span className="font-semibold text-surface-200">{topic.post_count}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-surface-500">Sentiment:</span>
              <span className={`font-semibold ${getSentimentColor(topic.avg_sentiment)}`}>
                {getSentimentLabel(topic.avg_sentiment)} ({topic.avg_sentiment?.toFixed(2) ?? '—'})
              </span>
            </div>
          </div>

          {/* Keywords */}
          {topic.top_keywords && topic.top_keywords.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {topic.top_keywords.map((keyword, idx) => (
                <span key={idx} className="keyword-pill">
                  {keyword}
                </span>
              ))}
            </div>
          )}
        </div>
      ) : (
        !isLoading && (
          <div className="glass-card p-6">
            <h1 className="text-xl font-bold text-surface-300">Topic #{id}</h1>
          </div>
        )
      )}

      {/* Error Banner */}
      {error && (
        <div className="error-banner" id="topic-error">
          <svg className="w-5 h-5 text-rose-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <p className="text-sm">{error.message || 'Failed to load topic posts.'}</p>
        </div>
      )}

      {/* Loading Skeletons */}
      {isLoading && (
        <div className="space-y-4">
          <div className="glass-card p-6 space-y-3">
            <div className="skeleton h-6 w-48 rounded" />
            <div className="skeleton h-4 w-32 rounded" />
            <div className="flex gap-2">
              <div className="skeleton h-6 w-16 rounded-full" />
              <div className="skeleton h-6 w-20 rounded-full" />
              <div className="skeleton h-6 w-14 rounded-full" />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="glass-card p-5 space-y-3">
                <div className="skeleton h-4 w-20 rounded" />
                <div className="skeleton h-4 w-full rounded" />
                <div className="skeleton h-3 w-2/3 rounded" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Posts Grid */}
      {!isLoading && (
        <div>
          <h2 className="text-sm font-semibold text-surface-300 uppercase tracking-wider mb-4">
            Posts in this topic ({posts?.length ?? 0})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(posts || []).map((post) => (
              <TrendCard key={post.id} post={post} />
            ))}
            {(!posts || posts.length === 0) && (
              <div className="col-span-2 glass-card p-8 text-center">
                <p className="text-surface-500">No posts found in this topic.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default TopicDetail;
