import useSWR from 'swr';

const API_BASE = import.meta.env.VITE_API_URL || '';

const fetcher = async (url) => {
  const response = await fetch(url);
  if (!response.ok) {
    const error = new Error('API request failed');
    error.status = response.status;
    try {
      const data = await response.json();
      error.message = data.detail || `HTTP ${response.status}`;
    } catch {
      error.message = `HTTP ${response.status}`;
    }
    throw error;
  }
  return response.json();
};

/**
 * Fetch trending posts with source and time range filters.
 * Revalidates every 5 minutes.
 */
export function useTrends(source = 'all', hours = 24, limit = 100) {
  const params = new URLSearchParams();
  if (source !== 'all') params.set('source', source);
  params.set('hours', String(hours));
  params.set('limit', String(limit));

  const { data, error, isLoading, mutate } = useSWR(
    `${API_BASE}/api/trends?${params.toString()}`,
    fetcher,
    { refreshInterval: 300000, revalidateOnFocus: false }
  );

  return { data, error, isLoading, mutate };
}

/**
 * Fetch topic clusters with time range filter.
 * Revalidates every 15 minutes.
 */
export function useTopics(hours = 24) {
  const params = new URLSearchParams({ hours: String(hours) });

  const { data, error, isLoading, mutate } = useSWR(
    `${API_BASE}/api/topics?${params.toString()}`,
    fetcher,
    { refreshInterval: 900000, revalidateOnFocus: false }
  );

  return { data, error, isLoading, mutate };
}

/**
 * Fetch posts belonging to a specific topic cluster.
 * Revalidates every 5 minutes.
 */
export function useTopicPosts(topicId) {
  const { data, error, isLoading, mutate } = useSWR(
    topicId ? `${API_BASE}/api/topics/${topicId}/posts` : null,
    fetcher,
    { refreshInterval: 300000, revalidateOnFocus: false }
  );

  return { data, error, isLoading, mutate };
}
