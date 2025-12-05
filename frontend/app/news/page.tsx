"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Newspaper,
  ExternalLink,
  Clock,
  Tag,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Rss,
  Settings,
  Filter
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';

interface NewsSource {
  id: number;
  name: string;
  url: string;
  description: string | null;
  icon_url: string | null;
  is_active: boolean;
  is_default: boolean;
  total_articles: number;
  last_fetched_at: string | null;
  last_fetch_status: string | null;
}

interface NewsArticle {
  id: number;
  source_id: number;
  source_name: string | null;
  title: string;
  url: string;
  author: string | null;
  original_summary: string | null;
  llm_summary: string | null;
  llm_key_points: string[] | null;
  llm_relevance_score: number | null;
  llm_processed: boolean;
  categories: string[] | null;
  related_cves: string[] | null;
  published_at: string | null;
  fetched_at: string;
}

interface NewsStats {
  total_sources: number;
  active_sources: number;
  total_articles: number;
  processed_articles: number;
  articles_with_cves: number;
  recent_articles_24h: number;
}

export default function NewsPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [sources, setSources] = useState<NewsSource[]>([]);
  const [stats, setStats] = useState<NewsStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalArticles, setTotalArticles] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [selectedSource, setSelectedSource] = useState<number | null>(null);
  const [showSources, setShowSources] = useState(false);
  const pageSize = 20;

  useEffect(() => {
    fetchData();
  }, [page, selectedSource]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch articles
      let articlesUrl = `${API_URL}/api/v1/news/articles?page=${page}&page_size=${pageSize}`;
      if (selectedSource) {
        articlesUrl += `&source_id=${selectedSource}`;
      }

      const [articlesRes, sourcesRes, statsRes] = await Promise.all([
        fetch(articlesUrl),
        fetch(`${API_URL}/api/v1/news/sources`),
        fetch(`${API_URL}/api/v1/news/stats`),
      ]);

      if (articlesRes.ok) {
        const data = await articlesRes.json();
        setArticles(data.articles);
        setTotalArticles(data.total);
        setHasMore(data.has_more);
      }

      if (sourcesRes.ok) {
        const data = await sourcesRes.json();
        setSources(data);
      }

      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Failed to fetch news data:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Unknown";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      vulnerability: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
      malware: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
      breach: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
      ransomware: "bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-400",
      apt: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400",
      policy: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
      tool: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    };
    return colors[category] || "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Newspaper className="h-8 w-8 text-blue-600" />
            Security News
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Aggregated security news from trusted sources, processed by AI
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSources(!showSources)}
            className="flex items-center gap-2"
          >
            <Settings className="h-4 w-4" />
            Sources
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchData()}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Articles</p>
                  <p className="text-2xl font-bold">{stats.total_articles.toLocaleString()}</p>
                </div>
                <Newspaper className="h-8 w-8 text-blue-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Active Sources</p>
                  <p className="text-2xl font-bold">{stats.active_sources}</p>
                </div>
                <Rss className="h-8 w-8 text-orange-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">AI Processed</p>
                  <p className="text-2xl font-bold">{stats.processed_articles.toLocaleString()}</p>
                </div>
                <Sparkles className="h-8 w-8 text-purple-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Last 24h</p>
                  <p className="text-2xl font-bold">{stats.recent_articles_24h}</p>
                </div>
                <Clock className="h-8 w-8 text-green-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Sources Panel */}
      {showSources && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Rss className="h-5 w-5" />
              News Sources
            </CardTitle>
            <CardDescription>
              Filter by source or view all feeds combined
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* All Sources Option */}
              <div
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedSource === null
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                    : "border-gray-200 dark:border-gray-700 hover:border-gray-300"
                }`}
                onClick={() => setSelectedSource(null)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                      <Newspaper className="h-3 w-3 text-white" />
                    </div>
                    <span className="font-medium">All Sources</span>
                  </div>
                  <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800">
                    Combined
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  View all news from every source, sorted by time
                </p>
                <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
                  <span>{stats?.total_articles || 0} total articles</span>
                  <span>{sources.length} sources</span>
                </div>
              </div>

              {/* Individual Sources */}
              {sources.map((source) => (
                <div
                  key={source.id}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedSource === source.id
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                      : "border-gray-200 dark:border-gray-700 hover:border-gray-300"
                  }`}
                  onClick={() => setSelectedSource(source.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      {source.icon_url ? (
                        <img
                          src={source.icon_url}
                          alt={source.name}
                          className="w-5 h-5 rounded"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      ) : (
                        <Rss className="h-5 w-5 text-gray-400" />
                      )}
                      <span className="font-medium">{source.name}</span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${
                      source.is_active
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-600"
                    }`}>
                      {source.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>
                  {source.description && (
                    <p className="text-sm text-gray-500 mt-2 line-clamp-2">
                      {source.description}
                    </p>
                  )}
                  <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
                    <span>{source.total_articles} articles</span>
                    {source.last_fetched_at && (
                      <span>Updated {formatDate(source.last_fetched_at)}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Articles List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : articles.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Newspaper className="h-12 w-12 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                No articles yet
              </h3>
              <p className="text-gray-500 mt-1">
                News articles will appear here once sources are configured and fetched.
              </p>
            </CardContent>
          </Card>
        ) : (
          articles.map((article) => (
            <Card key={article.id} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex flex-col md:flex-row md:items-start gap-4">
                  <div className="flex-1">
                    {/* Source and Date */}
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                      <span className="font-medium text-gray-700 dark:text-gray-300">
                        {article.source_name}
                      </span>
                      <span>•</span>
                      <Clock className="h-3 w-3" />
                      <span>{formatDate(article.published_at)}</span>
                      {article.llm_processed && (
                        <>
                          <span>•</span>
                          <span className="flex items-center gap-1 text-purple-600">
                            <Sparkles className="h-3 w-3" />
                            AI Processed
                          </span>
                        </>
                      )}
                    </div>

                    {/* Title */}
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group"
                    >
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 transition-colors flex items-start gap-2">
                        {article.title}
                        <ExternalLink className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-1" />
                      </h3>
                    </a>

                    {/* Summary */}
                    <p className="text-gray-600 dark:text-gray-400 mt-2 line-clamp-3">
                      {article.llm_summary || article.original_summary || "No summary available."}
                    </p>

                    {/* Key Points */}
                    {article.llm_key_points && article.llm_key_points.length > 0 && (
                      <ul className="mt-3 space-y-1">
                        {article.llm_key_points.slice(0, 3).map((point, idx) => (
                          <li key={idx} className="text-sm text-gray-500 flex items-start gap-2">
                            <span className="text-blue-500 mt-1">•</span>
                            {point}
                          </li>
                        ))}
                      </ul>
                    )}

                    {/* Tags */}
                    <div className="flex flex-wrap items-center gap-2 mt-4">
                      {/* Categories */}
                      {article.categories?.map((cat) => (
                        <span
                          key={cat}
                          className={`text-xs px-2 py-1 rounded-full ${getCategoryColor(cat)}`}
                        >
                          {cat}
                        </span>
                      ))}

                      {/* Related CVEs */}
                      {article.related_cves?.map((cve) => (
                        <a
                          key={cve}
                          href={`/vulnerabilities/${cve}`}
                          className="text-xs px-2 py-1 rounded-full bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 hover:bg-red-200 transition-colors flex items-center gap-1"
                        >
                          <AlertTriangle className="h-3 w-3" />
                          {cve}
                        </a>
                      ))}

                      {/* Relevance Score */}
                      {article.llm_relevance_score !== null && (
                        <span className="text-xs text-gray-400 ml-auto">
                          Relevance: {Math.round(article.llm_relevance_score * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalArticles > pageSize && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, totalArticles)} of {totalArticles} articles
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={!hasMore}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
