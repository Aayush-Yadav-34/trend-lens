const SOURCES = [
  { key: 'all', label: 'All Sources' },
  { key: 'reddit', label: 'Reddit' },
  { key: 'hn', label: 'Hacker News' },
  { key: 'github', label: 'GitHub' },
];

const TIME_RANGES = [
  { key: 6, label: '6h' },
  { key: 24, label: '24h' },
  { key: 48, label: '48h' },
  { key: 168, label: '7d' },
];

function FilterBar({ source, setSource, hours, setHours }) {
  return (
    <div className="glass-card p-4 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        {/* Source Filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-surface-500 uppercase tracking-wider mr-1">
            Source
          </span>
          <div className="flex gap-1.5">
            {SOURCES.map((s) => (
              <button
                key={s.key}
                id={`filter-source-${s.key}`}
                onClick={() => setSource(s.key)}
                className={`filter-btn ${source === s.key ? 'filter-btn-active' : ''}`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div className="hidden sm:block w-px h-8 bg-surface-700/50" />

        {/* Time Range Filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-surface-500 uppercase tracking-wider mr-1">
            Period
          </span>
          <div className="flex gap-1.5">
            {TIME_RANGES.map((t) => (
              <button
                key={t.key}
                id={`filter-time-${t.key}`}
                onClick={() => setHours(t.key)}
                className={`filter-btn ${hours === t.key ? 'filter-btn-active' : ''}`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default FilterBar;
