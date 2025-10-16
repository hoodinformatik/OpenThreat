"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Shield, AlertTriangle, ChevronLeft, ChevronRight, Filter } from "lucide-react";
import { formatDate, getSeverityBadgeColor } from "@/lib/utils";
import type { Vulnerability, PaginatedResponse } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';

export default function VulnerabilitiesPage() {
  const [data, setData] = useState<PaginatedResponse<Vulnerability> | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [severity, setSeverity] = useState<string>("");
  const [exploited, setExploited] = useState<string>("");
  const [sortBy, setSortBy] = useState("priority_score");

  useEffect(() => {
    fetchVulnerabilities();
  }, [page, severity, exploited, sortBy]);

  const fetchVulnerabilities = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: "20",
        sort_by: sortBy,
        sort_order: "desc",
      });

      if (severity) params.append("severity", severity);
      if (exploited) params.append("exploited", exploited);

      const res = await fetch(`${API_URL}/api/v1/vulnerabilities?${params}`);
      const json = await res.json();
      setData(json);
    } catch (error) {
      console.error("Failed to fetch vulnerabilities:", error);
    } finally {
      setLoading(false);
    }
  };

  const resetFilters = () => {
    setSeverity("");
    setExploited("");
    setSortBy("priority_score");
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Vulnerabilities</h1>
          <p className="text-gray-600 mt-1">
            Browse all tracked CVEs from multiple sources
          </p>
        </div>
        <Link href="/search">
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            Advanced Search
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Severity Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Severity
              </label>
              <select
                value={severity}
                onChange={(e) => {
                  setSeverity(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>

            {/* Exploited Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Exploitation Status
              </label>
              <select
                value={exploited}
                onChange={(e) => {
                  setExploited(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All</option>
                <option value="true">Exploited in Wild</option>
                <option value="false">Not Exploited</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="priority_score">Priority Score</option>
                <option value="cvss_score">CVSS Score</option>
                <option value="published_at">Published Date</option>
                <option value="modified_at">Modified Date</option>
              </select>
            </div>

            {/* Reset Button */}
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={resetFilters}
                className="w-full"
              >
                Reset Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading vulnerabilities...</p>
        </div>
      ) : data ? (
        <>
          {/* Stats */}
          <div className="flex items-center justify-between text-sm text-gray-600">
            <p>
              Showing {((page - 1) * 20) + 1} - {Math.min(page * 20, data.total)} of{" "}
              <span className="font-semibold">{data.total.toLocaleString()}</span> vulnerabilities
            </p>
            <p>
              Page {page} of {data.total_pages}
            </p>
          </div>

          {/* Vulnerability List */}
          <div className="space-y-4">
            {data.items.map((vuln) => (
              <Link
                key={vuln.cve_id}
                href={`/vulnerabilities/${vuln.cve_id}`}
              >
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="font-mono font-bold text-lg text-blue-600">
                            {vuln.cve_id}
                          </span>
                          {vuln.severity && (
                            <Badge className={getSeverityBadgeColor(vuln.severity)}>
                              {vuln.severity}
                            </Badge>
                          )}
                          {vuln.exploited_in_the_wild && (
                            <Badge className="bg-red-100 text-red-800 border-red-300">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              Exploited
                            </Badge>
                          )}
                        </div>

                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          {vuln.simple_title || vuln.title}
                        </h3>

                        {(vuln.simple_description || vuln.description) && (
                          <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                            {vuln.simple_description || vuln.description}
                          </p>
                        )}
                        
                        {!vuln.description && !vuln.simple_description && (
                          <p className="text-gray-500 text-sm italic mb-3">
                            No description available. Processing in background...
                          </p>
                        )}

                        <div className="flex items-center space-x-6 text-sm text-gray-500">
                          {vuln.cvss_score && (
                            <div className="flex items-center space-x-1">
                              <span className="font-medium">CVSS:</span>
                              <span className="font-semibold text-gray-900">
                                {vuln.cvss_score}
                              </span>
                            </div>
                          )}
                          {vuln.priority_score && (
                            <div className="flex items-center space-x-1">
                              <span className="font-medium">Priority:</span>
                              <span className="font-semibold text-gray-900">
                                {vuln.priority_score.toFixed(2)}
                              </span>
                            </div>
                          )}
                          {vuln.published_at && (
                            <div className="flex items-center space-x-1">
                              <span className="font-medium">Published:</span>
                              <span>{formatDate(vuln.published_at)}</span>
                            </div>
                          )}
                          {vuln.sources && vuln.sources.length > 0 && (
                            <div className="flex items-center space-x-1">
                              <span className="font-medium">Sources:</span>
                              <span>{vuln.sources.join(", ")}</span>
                            </div>
                          )}
                        </div>
                      </div>

                      <Shield className="h-6 w-6 text-gray-400 ml-4" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
            >
              <ChevronLeft className="h-4 w-4 mr-2" />
              Previous
            </Button>

            <div className="flex items-center space-x-2">
              {page > 2 && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setPage(1)}
                    size="sm"
                  >
                    1
                  </Button>
                  {page > 3 && <span className="text-gray-500">...</span>}
                </>
              )}

              {page > 1 && (
                <Button
                  variant="outline"
                  onClick={() => setPage(page - 1)}
                  size="sm"
                >
                  {page - 1}
                </Button>
              )}

              <Button variant="default" size="sm">
                {page}
              </Button>

              {page < data.total_pages && (
                <Button
                  variant="outline"
                  onClick={() => setPage(page + 1)}
                  size="sm"
                >
                  {page + 1}
                </Button>
              )}

              {page < data.total_pages - 1 && (
                <>
                  {page < data.total_pages - 2 && (
                    <span className="text-gray-500">...</span>
                  )}
                  <Button
                    variant="outline"
                    onClick={() => setPage(data.total_pages)}
                    size="sm"
                  >
                    {data.total_pages}
                  </Button>
                </>
              )}
            </div>

            <Button
              variant="outline"
              onClick={() => setPage(page + 1)}
              disabled={page === data.total_pages}
            >
              Next
              <ChevronRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-600">No vulnerabilities found.</p>
        </div>
      )}
    </div>
  );
}
