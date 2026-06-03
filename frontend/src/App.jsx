import { Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import TopicDetail from './pages/TopicDetail';

function App() {
  return (
    <div className="min-h-screen bg-surface-950">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-surface-800/50 bg-surface-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-500/25 group-hover:shadow-brand-500/40 transition-shadow">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <h1 className="text-xl font-bold gradient-text">Trend Lens</h1>
            </Link>
            <nav className="flex items-center gap-4">
              <Link
                to="/"
                className="text-sm font-medium text-surface-300 hover:text-surface-100 transition-colors"
              >
                Dashboard
              </Link>
              <a
                href="/api/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-surface-300 hover:text-surface-100 transition-colors"
              >
                API Docs
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/topic/:id" element={<TopicDetail />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-800/50 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-surface-500">
            Trend Lens — Real-time tech trends from Reddit, Hacker News & GitHub
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
