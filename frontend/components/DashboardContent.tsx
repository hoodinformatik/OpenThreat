"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { AlertTriangle, Shield, Clock, Calendar, Filter, X } from "lucide-react";
import Link from "next/link";
import { formatDate, getSeverityBadgeColor } from "@/lib/utils";
import { CVEVoteButton } from "@/components/CVEVoteButton";
import { fetchTrendingCVEs } from "@/lib/api";

const CLIENT_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';

// In-memory cache with timestamps
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_DURATION = 3 * 60 * 1000; // 3 minutes

function getCachedData(key: string) {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.data;
  }
  return null;
}

function setCachedData(key: string, data: any) {
  cache.set(key, { data, timestamp: Date.now() });
}

export function DashboardContent() {
  const [stats, setStats] = useState<any>(null);
  const [recentVulns, setRecentVulns] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Filter states
  const [showFilters, setShowFilters] = useState(false);
  const [severity, setSeverity] = useState("");
  const [exploited, setExploited] = useState("");
  const [isFiltering, setIsFiltering] = useState(false);

  // View mode: 'recent', 'hot', 'top'
  const [viewMode, setViewMode] = useState<'recent' | 'hot' | 'top'>('recent');

  // Track if we've already fetched to prevent double-fetching
  const hasFetched = useRef(false);

  useEffect(() => {
    // Only fetch once on mount
    if (!hasFetched.current) {
      hasFetched.current = true;
      fetchInitialData();
    }
  }, []);

  // Fetch trending data when viewMode changes
  useEffect(() => {
    if (viewMode !== 'recent') {
      fetchTrendingData();
    } else {
      // Reset to initial data when switching back to recent
      const cached = getCachedData('vulns:default');
      if (cached) {
        setRecentVulns(cached);
      } else {
        fetchFilteredVulns("", "");
      }
    }
  }, [viewMode]);

  const fetchTrendingData = async () => {
    setIsFiltering(true);
    try {
      const trendingType = viewMode === 'hot' ? 'hot' : 'top';
      const response = await fetchTrendingCVEs({
        trending_type: trendingType,
        time_range: 'this_week',
        page: 1,
        page_size: 20,
      });

      setRecentVulns(response);
    } catch (error) {
      console.error("Failed to fetch trending data:", error);
    } finally {
      setIsFiltering(false);
    }
  };

  const fetchInitialData = async () => {
    try {
      // Check cache first
      const cachedStats = getCachedData('stats');
      const cachedVulns = getCachedData('vulns:default');

      if (cachedStats && cachedVulns) {
        setStats(cachedStats);
        setRecentVulns(cachedVulns);
        setLoading(false);
        return;
      }

      // Fetch from API
      const [statsRes, vulnsRes] = await Promise.all([
        fetch(`${CLIENT_API_URL}/api/v1/stats`),
        fetch(`${CLIENT_API_URL}/api/v1/vulnerabilities?page_size=20&sort_by=published_at&sort_order=desc`)
      ]);

      const [statsData, vulnsData] = await Promise.all([
        statsRes.json(),
        vulnsRes.json()
      ]);

      // Cache the results
      setCachedData('stats', statsData);
      setCachedData('vulns:default', vulnsData);

      setStats(statsData);
      setRecentVulns(vulnsData);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFilteredVulns = async (newSeverity: string, newExploited: string) => {
    setIsFiltering(true);

    try {
      const cacheKey = `vulns:${newSeverity}:${newExploited}`;
      const cached = getCachedData(cacheKey);

      if (cached) {
        setRecentVulns(cached);
        setIsFiltering(false);
        return;
      }

      const params = new URLSearchParams({
        page_size: "20",
        sort_by: "published_at",
        sort_order: "desc",
      });

      if (newSeverity) params.append("severity", newSeverity);
      if (newExploited) params.append("exploited", newExploited);

      const res = await fetch(`${CLIENT_API_URL}/api/v1/vulnerabilities?${params}`);

      if (res.ok) {
        const data = await res.json();
        setCachedData(cacheKey, data);
        setRecentVulns(data);
      }
    } catch (error) {
      console.error("Failed to fetch filtered data:", error);
    } finally {
      setIsFiltering(false);
    }
  };

  const handleSeverityChange = (value: string) => {
    setSeverity(value);
    fetchFilteredVulns(value, exploited);
  };

  const handleExploitedChange = (value: string) => {
    setExploited(value);
    fetchFilteredVulns(severity, value);
  };

  const resetFilters = () => {
    setSeverity("");
    setExploited("");
    const cached = getCachedData('vulns:default');
    if (cached) {
      setRecentVulns(cached);
    } else {
      fetchFilteredVulns("", "");
    }
  };

  const hasActiveFilters = severity || exploited;

  if (loading || !stats || !recentVulns) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Clock className="h-12 w-12 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4 py-8">
        <h1 className="text-4xl font-bold text-gray-900">
          Latest Security Threats
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Stay informed about the latest vulnerabilities and security threats
        </p>
      </div>

      {/* Quick Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-4 bg-white rounded-lg border">
          <div className="text-2xl font-bold text-gray-900">{stats.total_vulnerabilities.toLocaleString()}</div>
          <div className="text-sm text-gray-600">Total CVEs</div>
        </div>
        <div className="text-center p-4 bg-white rounded-lg border">
          <div className="text-2xl font-bold text-red-600">{stats.exploited_vulnerabilities.toLocaleString()}</div>
          <div className="text-sm text-gray-600">Exploited</div>
        </div>
        <div className="text-center p-4 bg-white rounded-lg border">
          <div className="text-2xl font-bold text-orange-600">{stats.critical_vulnerabilities.toLocaleString()}</div>
          <div className="text-sm text-gray-600">Critical</div>
        </div>
        <div className="text-center p-4 bg-white rounded-lg border">
          <div className="text-2xl font-bold text-blue-600">{stats.recent_updates.toLocaleString()}</div>
          <div className="text-sm text-gray-600">Last 7 Days</div>
        </div>
      </div>

      {/* News Feed - Recent Vulnerabilities */}
      <div className="space-y-4">
        {/* Header - Mobile Optimized */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xl md:text-2xl font-bold text-gray-900">
              {viewMode === 'recent' ? 'Recent' : viewMode === 'hot' ? '🔥 Hot' : '🏆 Top'}
            </h2>
            <Link href="/vulnerabilities" className="text-sm text-blue-600 hover:text-blue-700 font-medium whitespace-nowrap">
              View All →
            </Link>
          </div>

          {/* View Mode Toggle + Filter - Mobile Optimized */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {/* View Mode Toggle - Compact */}
            <div className="flex gap-1 bg-gray-100 rounded-lg p-1 flex-shrink-0">
              <button
                onClick={() => setViewMode('recent')}
                className={`px-2 md:px-3 py-1.5 rounded-md text-xs md:text-sm font-medium transition-colors whitespace-nowrap ${
                  viewMode === 'recent'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Recent
              </button>
              <button
                onClick={() => setViewMode('hot')}
                className={`px-2 md:px-3 py-1.5 rounded-md text-xs md:text-sm font-medium transition-colors whitespace-nowrap ${
                  viewMode === 'hot'
                    ? 'bg-white text-orange-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🔥 Hot
              </button>
              <button
                onClick={() => setViewMode('top')}
                className={`px-2 md:px-3 py-1.5 rounded-md text-xs md:text-sm font-medium transition-colors whitespace-nowrap ${
                  viewMode === 'top'
                    ? 'bg-white text-yellow-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🏆 Top
              </button>
            </div>

            {/* Filter Button - Compact */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className={`flex-shrink-0 ${hasActiveFilters ? "border-blue-600 text-blue-600" : ""}`}
            >
              <Filter className="h-4 w-4 md:mr-2" />
              <span className="hidden md:inline">Filter</span>
              {hasActiveFilters && <span className="ml-1 md:ml-2 bg-blue-600 text-white rounded-full w-2 h-2 md:w-auto md:h-auto md:px-2 md:py-0.5 text-xs">•</span>}
            </Button>
          </div>
        </div>

        {/* Minimalist Filter Bar */}
        {showFilters && (
          <Card className="p-4 bg-gradient-to-br from-gray-50 to-white border-gray-200">
            <div className="flex flex-wrap items-center gap-3">
              {/* Severity Filter */}
              <Select
                value={severity}
                onChange={handleSeverityChange}
                disabled={isFiltering}
                placeholder="All Severities"
                options={[
                  { value: "", label: "All Severities" },
                  { value: "CRITICAL", label: "Critical" },
                  { value: "HIGH", label: "High" },
                  { value: "MEDIUM", label: "Medium" },
                  { value: "LOW", label: "Low" },
                ]}
                className="w-48"
              />

              {/* Exploited Filter */}
              <Select
                value={exploited}
                onChange={handleExploitedChange}
                disabled={isFiltering}
                placeholder="All CVEs"
                options={[
                  { value: "", label: "All CVEs" },
                  { value: "true", label: "Exploited Only" },
                  { value: "false", label: "Not Exploited" },
                ]}
                className="w-48"
              />

              {/* Reset Button */}
              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetFilters}
                  disabled={isFiltering}
                  className="text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
                >
                  <X className="h-4 w-4 mr-1" />
                  Reset
                </Button>
              )}

              {/* Results Count */}
              <span className="text-sm text-gray-600 ml-auto font-medium">
                {isFiltering ? "Loading..." : `${recentVulns.total} results`}
              </span>
            </div>
          </Card>
        )}

        <div className="space-y-4">
          {recentVulns.items.map((vuln: any) => {
            // Use LLM-generated content if available, otherwise fall back to original
            const displayTitle = vuln.simple_title || vuln.title;
            const displayDescription = vuln.simple_description || vuln.description;

            return (
              <Link
                key={vuln.cve_id}
                href={`/vulnerabilities/${vuln.cve_id}`}
                className="block"
              >
                <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                  <CardContent className="p-6">
                    <div className="flex gap-4">
                      {/* Vote Buttons */}
                      <div className="flex-shrink-0" onClick={(e) => e.preventDefault()}>
                        <CVEVoteButton
                          cveId={vuln.cve_id}
                          initialUpvotes={vuln.upvotes || 0}
                          initialDownvotes={vuln.downvotes || 0}
                          compact={true}
                        />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        {/* Article Title */}
                        <h3 className="text-xl font-bold text-gray-900 hover:text-blue-600 transition-colors mb-3">
                          {displayTitle}
                        </h3>

                    {/* Article Description */}
                    <p className="text-gray-700 mb-4 line-clamp-3">
                      {displayDescription}
                    </p>

                    {/* Metadata Row */}
                    <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
                      {/* CVE ID */}
                      <span className="font-mono font-semibold text-blue-600">
                        {vuln.cve_id}
                      </span>

                      {/* Severity Badge */}
                      {vuln.severity && vuln.severity !== 'UNKNOWN' && (
                        <Badge className={getSeverityBadgeColor(vuln.severity)}>
                          {vuln.severity}
                        </Badge>
                      )}

                      {/* Exploited Badge */}
                      {vuln.exploited_in_the_wild && (
                        <Badge className="bg-red-100 text-red-800 border-red-300">
                          <AlertTriangle className="h-3 w-3 mr-1" />
                          Exploited
                        </Badge>
                      )}

                      {/* CVSS Score */}
                      {vuln.cvss_score && (
                        <span className="flex items-center gap-1">
                          <Shield className="h-3 w-3" />
                          {vuln.cvss_score}
                        </span>
                      )}

                      {/* Date */}
                      {vuln.published_at && (
                        <span className="flex items-center gap-1 ml-auto text-gray-500">
                          <Calendar className="h-3 w-3" />
                          {formatDate(vuln.published_at)}
                        </span>
                      )}

                      {/* Modified Date as fallback */}
                      {!vuln.published_at && vuln.modified_at && (
                        <span className="flex items-center gap-1 ml-auto text-gray-500">
                          <Clock className="h-3 w-3" />
                          {formatDate(vuln.modified_at)}
                        </span>
                      )}
                    </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
