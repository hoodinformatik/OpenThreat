'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, Flame, Trophy, Calendar, Clock, TrendingDown } from 'lucide-react';
import Link from 'next/link';
import { fetchTrendingCVEs, type Vulnerability, type TimeRange, type TrendingType } from '@/lib/api';
import { CVEVoteButton } from './CVEVoteButton';

interface TrendingCVEsProps {
  defaultType?: TrendingType;
  defaultTimeRange?: TimeRange;
  limit?: number;
}

export function TrendingCVEs({
  defaultType = 'hot',
  defaultTimeRange = 'this_week',
  limit = 10
}: TrendingCVEsProps) {
  const [trendingType, setTrendingType] = useState<TrendingType>(defaultType);
  const [timeRange, setTimeRange] = useState<TimeRange>(defaultTimeRange);
  const [cves, setCves] = useState<Vulnerability[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTrendingCVEs();
  }, [trendingType, timeRange]);

  const loadTrendingCVEs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetchTrendingCVEs({
        trending_type: trendingType,
        time_range: timeRange,
        page: 1,
        page_size: limit,
      });
      setCves(response.items);
    } catch (err) {
      setError('Failed to load trending CVEs');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'LOW':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300';
    }
  };

  const timeRangeLabels: Record<TimeRange, string> = {
    today: 'Today',
    this_week: 'This Week',
    this_month: 'This Month',
    all_time: 'All Time',
  };

  const timeRangeIcons: Record<TimeRange, React.ReactNode> = {
    today: <Clock className="h-4 w-4" />,
    this_week: <Calendar className="h-4 w-4" />,
    this_month: <Calendar className="h-4 w-4" />,
    all_time: <TrendingUp className="h-4 w-4" />,
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          {trendingType === 'hot' ? (
            <Flame className="h-6 w-6 text-orange-500" />
          ) : (
            <Trophy className="h-6 w-6 text-yellow-500" />
          )}
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {trendingType === 'hot' ? 'Hot CVEs' : 'Top CVEs'}
          </h2>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-3 mb-6">
        {/* Trending Type Toggle */}
        <div className="flex gap-2 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => setTrendingType('hot')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              trendingType === 'hot'
                ? 'bg-white dark:bg-gray-800 text-orange-600 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            <Flame className="h-4 w-4 inline mr-1" />
            Hot
          </button>
          <button
            onClick={() => setTrendingType('top')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              trendingType === 'top'
                ? 'bg-white dark:bg-gray-800 text-yellow-600 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            <Trophy className="h-4 w-4 inline mr-1" />
            Top
          </button>
        </div>

        {/* Time Range Selector */}
        <div className="flex gap-2 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          {(['today', 'this_week', 'this_month', 'all_time'] as TimeRange[]).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                timeRange === range
                  ? 'bg-white dark:bg-gray-800 text-blue-600 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              {timeRangeLabels[range]}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse flex gap-4">
              <div className="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-8 text-red-600 dark:text-red-400">
          {error}
        </div>
      ) : cves.length === 0 ? (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No trending CVEs found for this time period.
        </div>
      ) : (
        <div className="space-y-3">
          {cves.map((cve, index) => (
            <Link
              key={cve.cve_id}
              href={`/vulnerabilities/${cve.cve_id}`}
              className="flex gap-4 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-md transition-all group"
            >
              {/* Rank & Vote */}
              <div className="flex flex-col items-center gap-2">
                <div className="text-2xl font-bold text-gray-400 dark:text-gray-600">
                  #{index + 1}
                </div>
                <CVEVoteButton
                  cveId={cve.cve_id}
                  initialUpvotes={cve.upvotes}
                  initialDownvotes={cve.downvotes}
                  compact
                />
              </div>

              {/* CVE Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {cve.cve_id}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                      {cve.simple_title || cve.title}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    {cve.severity && (
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(cve.severity)}`}>
                        {cve.severity}
                      </span>
                    )}
                    {cve.cvss_score && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        CVSS: {cve.cvss_score.toFixed(1)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Badges */}
                <div className="flex flex-wrap gap-2 mt-2">
                  {cve.exploited_in_the_wild && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
                      <TrendingDown className="h-3 w-3 mr-1" />
                      Exploited in Wild
                    </span>
                  )}
                  {cve.sources && cve.sources.length > 0 && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Sources: {cve.sources.join(', ')}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* View All Link */}
      {!isLoading && cves.length > 0 && (
        <div className="mt-6 text-center">
          <Link
            href={`/trending?type=${trendingType}&range=${timeRange}`}
            className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline font-medium"
          >
            View All Trending CVEs
            <TrendingUp className="h-4 w-4" />
          </Link>
        </div>
      )}
    </div>
  );
}
