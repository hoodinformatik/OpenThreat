"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Shield, Clock, Calendar, Filter, X, Search, ChevronLeft, ChevronRight } from "lucide-react";
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
  const [recentVulns, setRecentVulns] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Filter states
  const [showFilters, setShowFilters] = useState(false);
  const [severity, setSeverity] = useState("");
  const [exploited, setExploited] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isFiltering, setIsFiltering] = useState(false);
  const [page, setPage] = useState(1);
  const [isSearchMode, setIsSearchMode] = useState(false);

  // View mode: 'recent', 'hot', 'top'
  const [viewMode, setViewMode] = useState<'recent' | 'hot' | 'top'>('recent');

  // Track if we've already fetched to prevent double-fetching
  const hasFetched = useRef(false);

  useEffect(() => {
    if (!hasFetched.current) {
      hasFetched.current = true;
      fetchInitialData();
    }
  }, []);

  useEffect(() => {
    if (viewMode !== 'recent') {
      fetchTrendingData();
    } else if (!isSearchMode) {
      const cached = getCachedData('vulns:default');
      if (cached) {
        setRecentVulns(cached);
      } else {
        fetchFilteredVulns("", "", 1, "");
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
      const cachedVulns = getCachedData('vulns:default');

      if (cachedVulns) {
        setRecentVulns(cachedVulns);
        setLoading(false);
        return;
      }

      const res = await fetch(`${CLIENT_API_URL}/api/v1/vulnerabilities?page_size=20&sort_by=published_at&sort_order=desc`);
      const vulnsData = await res.json();

      setCachedData('vulns:default', vulnsData);
      setRecentVulns(vulnsData);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFilteredVulns = async (newSeverity: string, newExploited: string, newPage: number = 1, query: string = "") => {
    setIsFiltering(true);

    try {
      if (query) {
        const params = new URLSearchParams({
          page: newPage.toString(),
          page_size: "20",
        });
        params.append("q", query);
        if (newSeverity) params.append("severity", newSeverity);
        if (newExploited) params.append("exploited", newExploited);

        const res = await fetch(`${CLIENT_API_URL}/api/v1/search?${params}`);
        if (res.ok) {
          const data = await res.json();
          setRecentVulns(data);
          setIsSearchMode(true);
        }
      } else {
        const cacheKey = `vulns:${newSeverity}:${newExploited}:${newPage}`;
        const cached = getCachedData(cacheKey);

        if (cached && newPage === 1) {
          setRecentVulns(cached);
          setIsFiltering(false);
          setIsSearchMode(false);
          return;
        }

        const params = new URLSearchParams({
          page: newPage.toString(),
          page_size: "20",
          sort_by: "published_at",
          sort_order: "desc",
        });

        if (newSeverity) params.append("severity", newSeverity);
        if (newExploited) params.append("exploited", newExploited);

        const res = await fetch(`${CLIENT_API_URL}/api/v1/vulnerabilities?${params}`);

        if (res.ok) {
          const data = await res.json();
          if (newPage === 1) {
            setCachedData(cacheKey, data);
          }
          setRecentVulns(data);
          setIsSearchMode(false);
        }
      }
    } catch (error) {
      console.error("Failed to fetch filtered data:", error);
    } finally {
      setIsFiltering(false);
    }
  };

  const handleSeverityChange = (value: string) => {
    setSeverity(value);
    setPage(1);
    fetchFilteredVulns(value, exploited, 1, searchQuery);
  };

  const handleExploitedChange = (value: string) => {
    setExploited(value);
    setPage(1);
    fetchFilteredVulns(severity, value, 1, searchQuery);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setViewMode('recent');
    fetchFilteredVulns(severity, exploited, 1, searchQuery);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    fetchFilteredVulns(severity, exploited, newPage, searchQuery);
    window.scrollTo({ top: 300, behavior: 'smooth' });
  };

  const resetFilters = () => {
    setSeverity("");
    setExploited("");
    setSearchQuery("");
    setPage(1);
    setIsSearchMode(false);
    const cached = getCachedData('vulns:default');
    if (cached) {
      setRecentVulns(cached);
    } else {
      fetchFilteredVulns("", "", 1, "");
    }
  };

  const hasActiveFilters = severity || exploited || searchQuery;

  if (loading || !recentVulns) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Clock className="h-12 w-12 animate-spin mx-auto mb-4 text-blue-600 dark:text-blue-400" />
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Hero Section with Search */}
      <div className="text-center space-y-6 py-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
          Latest Security Threats
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          Stay informed about the latest vulnerabilities and security threats
        </p>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="max-w-2xl mx-auto">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search CVE ID, title, description, vendor, product..."
              className="w-full pl-12 pr-24 py-3 border border-gray-300 dark:border-gray-600 rounded-full bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
            />
            <Button
              type="submit"
              disabled={isFiltering}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 rounded-full px-6"
            >
              Search
            </Button>
          </div>
        </form>
      </div>

      {/* CVE List Section */}
      <div className="space-y-4">
        {/* Header */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-white">
              {isSearchMode ? 'Search Results' : viewMode === 'recent' ? 'Recent CVEs' : viewMode === 'hot' ? '🔥 Hot CVEs' : '🏆 Top CVEs'}
            </h2>
            {recentVulns && (
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {recentVulns.total?.toLocaleString() || 0} results
              </span>
            )}
          </div>

          {/* View Mode Toggle + Filter */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 flex-shrink-0">
              <button
                onClick={() => { setViewMode('recent'); setPage(1); }}
                className={`px-2 md:px-3 py-1.5 rounded-md text-xs md:text-sm font-medium transition-colors whitespace-nowrap ${
                  viewMode === 'recent'
                    ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                Recent
              </button>
              <button
                onClick={() => { setViewMode('hot'); setPage(1); }}
                className={`px-2 md:px-3 py-1.5 rounded-md text-xs md:text-sm font-medium transition-colors whitespace-nowrap ${
                  viewMode === 'hot'
                    ? 'bg-white dark:bg-gray-700 text-orange-600 dark:text-orange-400 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                🔥 Hot
              </button>
              <button
                onClick={() => { setViewMode('top'); setPage(1); }}
                className={`px-2 md:px-3 py-1.5 rounded-md text-xs md:text-sm font-medium transition-colors whitespace-nowrap ${
                  viewMode === 'top'
                    ? 'bg-white dark:bg-gray-700 text-yellow-600 dark:text-yellow-400 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                🏆 Top
              </button>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className={`flex-shrink-0 ${hasActiveFilters ? "border-blue-600 dark:border-blue-400 text-blue-600 dark:text-blue-400" : ""}`}
            >
              <Filter className="h-4 w-4 md:mr-2" />
              <span className="hidden md:inline">Filter</span>
              {hasActiveFilters && <span className="ml-1 md:ml-2 bg-blue-600 text-white rounded-full w-2 h-2 md:w-auto md:h-auto md:px-2 md:py-0.5 text-xs">•</span>}
            </Button>
          </div>
        </div>

        {/* Filter Bar */}
        {showFilters && (
          <Card className="p-4 bg-gray-50 dark:bg-gray-800">
            <div className="flex flex-wrap items-center gap-3">
              <select
                value={severity}
                onChange={(e) => handleSeverityChange(e.target.value)}
                disabled={isFiltering}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <option value="">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>

              <select
                value={exploited}
                onChange={(e) => handleExploitedChange(e.target.value)}
                disabled={isFiltering}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <option value="">All CVEs</option>
                <option value="true">Exploited Only</option>
                <option value="false">Not Exploited</option>
              </select>

              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetFilters}
                  disabled={isFiltering}
                  className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                >
                  <X className="h-4 w-4 mr-1" />
                  Reset
                </Button>
              )}

              <span className="text-sm text-gray-600 dark:text-gray-400 ml-auto">
                {isFiltering ? "Loading..." : `Page ${page} of ${recentVulns.total_pages || 1}`}
              </span>
            </div>
          </Card>
        )}

        {/* CVE List */}
        <div className="space-y-4">
          {recentVulns.items.map((vuln: any) => {
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
                      <div className="flex-shrink-0" onClick={(e) => e.preventDefault()}>
                        <CVEVoteButton
                          cveId={vuln.cve_id}
                          initialUpvotes={vuln.upvotes || 0}
                          initialDownvotes={vuln.downvotes || 0}
                          compact={true}
                        />
                      </div>

                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors mb-3">
                          {displayTitle}
                        </h3>

                        <p className="text-gray-700 dark:text-gray-300 mb-4 line-clamp-3">
                          {displayDescription}
                        </p>

                        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                          <span className="font-mono font-semibold text-blue-600 dark:text-blue-400">
                            {vuln.cve_id}
                          </span>

                          {vuln.severity && vuln.severity !== 'UNKNOWN' && (
                            <Badge className={getSeverityBadgeColor(vuln.severity)}>
                              {vuln.severity}
                            </Badge>
                          )}

                          {vuln.exploited_in_the_wild && (
                            <Badge className="bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400 border-red-300 dark:border-red-700">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              Exploited
                            </Badge>
                          )}

                          {vuln.cvss_score && (
                            <span className="flex items-center gap-1">
                              <Shield className="h-3 w-3" />
                              {vuln.cvss_score}
                            </span>
                          )}

                          {vuln.published_at && (
                            <span className="flex items-center gap-1 ml-auto text-gray-500 dark:text-gray-500">
                              <Calendar className="h-3 w-3" />
                              {formatDate(vuln.published_at)}
                            </span>
                          )}

                          {!vuln.published_at && vuln.modified_at && (
                            <span className="flex items-center gap-1 ml-auto text-gray-500 dark:text-gray-500">
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

        {/* Pagination */}
        {recentVulns && recentVulns.total_pages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-6">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1 || isFiltering}
            >
              <ChevronLeft className="h-4 w-4" />
              <span className="hidden sm:inline ml-1">Previous</span>
            </Button>

            <div className="flex items-center gap-1">
              {page > 2 && (
                <>
                  <Button variant="outline" size="sm" onClick={() => handlePageChange(1)}>1</Button>
                  {page > 3 && <span className="text-gray-400 px-1">...</span>}
                </>
              )}

              {page > 1 && (
                <Button variant="outline" size="sm" onClick={() => handlePageChange(page - 1)}>
                  {page - 1}
                </Button>
              )}

              <Button variant="default" size="sm" disabled>{page}</Button>

              {page < recentVulns.total_pages && (
                <Button variant="outline" size="sm" onClick={() => handlePageChange(page + 1)}>
                  {page + 1}
                </Button>
              )}

              {page < recentVulns.total_pages - 1 && (
                <>
                  {page < recentVulns.total_pages - 2 && <span className="text-gray-400 px-1">...</span>}
                  <Button variant="outline" size="sm" onClick={() => handlePageChange(recentVulns.total_pages)}>
                    {recentVulns.total_pages}
                  </Button>
                </>
              )}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(page + 1)}
              disabled={page === recentVulns.total_pages || isFiltering}
            >
              <span className="hidden sm:inline mr-1">Next</span>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
