"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  Users,
  Globe,
  TrendingUp,
  Calendar,
  Eye,
  Clock,
  RefreshCw,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AnalyticsData {
  total_views: number;
  unique_visitors: number;
  views_today: number;
  views_this_week: number;
  views_this_month: number;
  views_this_year: number;
  top_pages: { path: string; views: number }[];
  views_by_day: { date: string; views: number }[];
  views_by_country: { country: string; views: number }[];
  views_by_device: { device: string; views: number }[];
  views_by_browser: { browser: string; views: number }[];
  recent_views: {
    path: string;
    country: string | null;
    device: string | null;
    browser: string | null;
    created_at: string | null;
  }[];
}


function StatCard({
  title,
  value,
  icon,
  description,
  trend,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description?: string;
  trend?: { value: number; positive: boolean };
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between">
        <div className="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
          {icon}
        </div>
        {trend && (
          <div
            className={`flex items-center text-sm ${
              trend.positive ? "text-green-600" : "text-red-600"
            }`}
          >
            <TrendingUp
              className={`h-4 w-4 mr-1 ${!trend.positive && "rotate-180"}`}
            />
            {trend.value}%
          </div>
        )}
      </div>
      <div className="mt-4">
        <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
          {typeof value === "number" ? value.toLocaleString() : value}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{title}</p>
        {description && (
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}

function formatDate(dateString: string) {
  const date = new Date(dateString);
  return date.toLocaleDateString("de-DE", { month: "short", day: "numeric" });
}

function getCountryFlag(countryCode: string | null) {
  if (!countryCode || countryCode.length !== 2) return "🌍";
  const codePoints = countryCode
    .toUpperCase()
    .split("")
    .map((char) => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}

export default function SiteStatsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${API_URL}/api/v1/analytics/stats?days=${days}`
      );
      if (!response.ok) throw new Error("Failed to fetch analytics");
      const data = await response.json();
      setAnalytics(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [days]);

  if (loading && !analytics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
        <p className="text-red-600 dark:text-red-400">
          Error loading analytics: {error}
        </p>
        <button
          onClick={fetchAnalytics}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <BarChart3 className="h-8 w-8 text-blue-600" />
            Site Statistics
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Visitor analytics and site performance metrics
          </p>
        </div>
        <div className="flex items-center gap-4 mt-4 md:mt-0">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
          <button
            onClick={fetchAnalytics}
            className="p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            title="Refresh"
          >
            <RefreshCw
              className={`h-5 w-5 text-gray-600 dark:text-gray-400 ${
                loading ? "animate-spin" : ""
              }`}
            />
          </button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Page Views"
          value={analytics?.total_views || 0}
          icon={<Eye className="h-6 w-6 text-blue-600" />}
          description="All time"
        />
        <StatCard
          title="Unique Visitors"
          value={analytics?.unique_visitors || 0}
          icon={<Users className="h-6 w-6 text-green-600" />}
          description="Based on session ID"
        />
        <StatCard
          title="Views Today"
          value={analytics?.views_today || 0}
          icon={<Calendar className="h-6 w-6 text-orange-600" />}
        />
        <StatCard
          title="Views This Month"
          value={analytics?.views_this_month || 0}
          icon={<TrendingUp className="h-6 w-6 text-purple-600" />}
        />
      </div>

      {/* Time Period Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3 mb-2">
            <Clock className="h-5 w-5 text-blue-600" />
            <span className="text-sm text-gray-500 dark:text-gray-400">This Week</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {(analytics?.views_this_week || 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3 mb-2">
            <Calendar className="h-5 w-5 text-green-600" />
            <span className="text-sm text-gray-500 dark:text-gray-400">This Month</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {(analytics?.views_this_month || 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="h-5 w-5 text-purple-600" />
            <span className="text-sm text-gray-500 dark:text-gray-400">This Year</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {(analytics?.views_this_year || 0).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Views Over Time */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Views Over Time
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analytics?.views_by_day || []}>
                  <defs>
                    <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    className="stroke-gray-200 dark:stroke-gray-700"
                  />
                  <XAxis
                    dataKey="date"
                    tickFormatter={formatDate}
                    className="text-xs"
                    stroke="#9CA3AF"
                  />
                  <YAxis className="text-xs" stroke="#9CA3AF" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "var(--tooltip-bg, #1F2937)",
                      border: "none",
                      borderRadius: "8px",
                      color: "#fff",
                    }}
                    labelFormatter={(label) => formatDate(label)}
                  />
                  <Area
                    type="monotone"
                    dataKey="views"
                    stroke="#3B82F6"
                    fillOpacity={1}
                    fill="url(#colorViews)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top Pages */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Top Pages
            </h3>
            <div className="space-y-3">
              {analytics?.top_pages && analytics.top_pages.length > 0 ? (
                analytics.top_pages.slice(0, 8).map((page, index) => (
                  <div
                    key={page.path}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-500 dark:text-gray-400 w-6">
                        {index + 1}.
                      </span>
                      <span className="text-sm text-gray-900 dark:text-white truncate max-w-[200px]">
                        {page.path === "/" ? "Homepage" : page.path}
                      </span>
                    </div>
                    <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                      {page.views.toLocaleString()}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                  No page views yet
                </p>
              )}
            </div>
          </div>
      </div>

      {/* Countries */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Globe className="h-5 w-5 text-blue-600" />
          Top Countries
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
          {analytics?.views_by_country && analytics.views_by_country.length > 0 ? (
            analytics.views_by_country.map((country) => (
              <div
                key={country.country}
                className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
              >
                <span className="text-2xl">{getCountryFlag(country.country)}</span>
                <div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white block">
                    {country.country || "Unknown"}
                  </span>
                  <span className="text-xs text-blue-600 dark:text-blue-400">
                    {country.views.toLocaleString()} views
                  </span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 dark:text-gray-400 text-center py-4 col-span-full">
              No geographic data yet
            </p>
          )}
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
            <BarChart3 className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h4 className="font-semibold text-blue-900 dark:text-blue-100">
              Privacy-Friendly Analytics
            </h4>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
              OpenThreat uses privacy-respecting analytics. We don&apos;t track
              personal information, use cookies for tracking, or share data
              with third parties. All visitor data is anonymized and stored
              securely.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
