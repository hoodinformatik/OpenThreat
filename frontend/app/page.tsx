"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Shield, TrendingUp, Clock, Calendar, Filter, X } from "lucide-react";
import Link from "next/link";
import { formatDate, getSeverityBadgeColor } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';

export default function HomePage() {
  const [stats, setStats] = useState<any>(null);
  const [recentVulns, setRecentVulns] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  // Filter states
  const [showFilters, setShowFilters] = useState(false);
  const [severity, setSeverity] = useState("");
  const [exploited, setExploited] = useState("");

  useEffect(() => {
    fetchData();
  }, [severity, exploited]);

  const fetchData = async () => {
    try {
      // Only show loading on initial load
      if (!stats || !recentVulns) {
        setLoading(true);
      }

      console.log("Fetching from:", API_URL);

      // Fetch vulnerabilities params
      const params = new URLSearchParams({
        page_size: "20",
        sort_by: "published_at",
        sort_order: "desc",
      });

      if (severity) params.append("severity", severity);
      if (exploited) params.append("exploited", exploited);

      const vulnsUrl = `${API_URL}/api/v1/vulnerabilities?${params}`;
      
      // Fetch both in parallel instead of sequentially
      const [statsRes, vulnsRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/stats`),
        fetch(vulnsUrl)
      ]);

      const [statsData, vulnsData] = await Promise.all([
        statsRes.json(),
        vulnsRes.json()
      ]);

      console.log("Stats loaded:", statsData);
      console.log("Vulnerabilities loaded:", vulnsData.items?.length, "items");
      
      setStats(statsData);
      setRecentVulns(vulnsData);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const resetFilters = () => {
    setSeverity("");
    setExploited("");
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
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Recent Vulnerabilities</h2>
          <div className="flex items-center gap-3">
            {/* Filter Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className={hasActiveFilters ? "border-blue-600 text-blue-600" : ""}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filter
              {hasActiveFilters && <span className="ml-2 bg-blue-600 text-white rounded-full px-2 py-0.5 text-xs">•</span>}
            </Button>
            <Link href="/vulnerabilities" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
              View All →
            </Link>
          </div>
        </div>

        {/* Minimalist Filter Bar */}
        {showFilters && (
          <Card className="p-4 bg-gray-50">
            <div className="flex flex-wrap items-center gap-3">
              {/* Severity Filter */}
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>

              {/* Exploited Filter */}
              <select
                value={exploited}
                onChange={(e) => setExploited(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All CVEs</option>
                <option value="true">Exploited Only</option>
                <option value="false">Not Exploited</option>
              </select>

              {/* Reset Button */}
              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetFilters}
                  className="text-gray-600 hover:text-gray-900"
                >
                  <X className="h-4 w-4 mr-1" />
                  Reset
                </Button>
              )}

              {/* Results Count */}
              <span className="text-sm text-gray-600 ml-auto">
                {recentVulns.total} results
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
