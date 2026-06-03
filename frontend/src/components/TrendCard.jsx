const SOURCE_BADGES = {
  reddit: { className: 'badge-reddit', label: 'Reddit', icon: '🟠' },
  hn: { className: 'badge-hn', label: 'HN', icon: '🟡' },
  github: { className: 'badge-github', label: 'GitHub', icon: '⚫' },
};

function getSentimentClass(sentiment) {
  if (sentiment > 0.05) return 'sentiment-positive';
  if (sentiment < -0.05) return 'sentiment-negative';
  return 'sentiment-neutral';
}

function TrendCard({ post }) {
  const badge = SOURCE_BADGES[post.source] || SOURCE_BADGES.github;

  return (
    <article
      id={`trend-card-${post.id}`}
      className="glass-card-hover p-5 flex flex-col gap-3 animate-slide-up"
    >
      {/* Header: Badge + Sentiment */}
      <div className="flex items-center justify-between">
        <span className={`badge ${badge.className}`}>
          {badge.icon} {badge.label}
        </span>
        <div className="flex items-center gap-2">
          <span
            className={`sentiment-dot ${getSentimentClass(post.sentiment)}`}
            title={`Sentiment: ${post.sentiment?.toFixed(2) ?? 'N/A'}`}
          />
          <span className="text-xs text-surface-500">
            {post.sentiment?.toFixed(2) ?? '—'}
          </span>
        </div>
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold text-surface-100 leading-snug">
        {post.url ? (
          <a
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-brand-400 transition-colors"
          >
            {post.title}
          </a>
        ) : (
          post.title
        )}
      </h3>

      {/* Meta */}
      <div className="flex items-center gap-4 text-xs text-surface-500">
        <span className="flex items-center gap-1">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
          </svg>
          {post.score?.toLocaleString() ?? 0}
        </span>
        <span>by {post.author || 'unknown'}</span>
        {post.fetched_at && (
          <span className="ml-auto">
            {new Date(post.fetched_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        )}
      </div>
    </article>
  );
}

export default TrendCard;
