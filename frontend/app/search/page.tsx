"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Search, Shield, AlertTriangle, X } from "lucide-react";
import { formatDate, getSeverityBadgeColor } from "@/lib/utils";
import type { Vulnerability, PaginatedResponse } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("");
  const [exploited, setExploited] = useState("");
  const [vendor, setVendor] = useState("");
  const [product, setProduct] = useState("");
  const [minCvss, setMinCvss] = useState("");
  const [maxCvss, setMaxCvss] = useState("");
  const [publishedAfter, setPublishedAfter] = useState("");
  const [publishedBefore, setPublishedBefore] = useState("");
  
  const [results, setResults] = useState<PaginatedResponse<Vulnerability> | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    
    setLoading(true);
    setSearched(true);

    try {
      const params = new URLSearchParams({
        page: "1",
        page_size: "20",
      });

      if (query) params.append("q", query);
      if (severity) params.append("severity", severity);
      if (exploited) params.append("exploited", exploited);
      if (vendor) params.append("vendor", vendor);
      if (product) params.append("product", product);
      if (minCvss) params.append("min_cvss", minCvss);
      if (maxCvss) params.append("max_cvss", maxCvss);
      if (publishedAfter) params.append("published_after", publishedAfter);
      if (publishedBefore) params.append("published_before", publishedBefore);

      const res = await fetch(`${API_URL}/api/v1/search?${params}`);
      const json = await res.json();
      setResults(json);
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const resetSearch = () => {
    setQuery("");
    setSeverity("");
    setExploited("");
    setVendor("");
    setProduct("");
    setMinCvss("");
    setMaxCvss("");
    setPublishedAfter("");
    setPublishedBefore("");
    setResults(null);
    setSearched(false);
  };

  const activeFiltersCount = [
    query,
    severity,
    exploited,
    vendor,
    product,
    minCvss,
    maxCvss,
    publishedAfter,
    publishedBefore,
  ].filter(Boolean).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Advanced Search</h1>
        <p className="text-gray-600 mt-1">
          Search vulnerabilities with multiple filters and criteria
        </p>
      </div>

      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle>Search Criteria</CardTitle>
          <CardDescription>
            {activeFiltersCount > 0
              ? `${activeFiltersCount} filter${activeFiltersCount > 1 ? "s" : ""} active`
              : "Enter your search criteria below"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-6">
            {/* Text Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Query
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="CVE ID, title, or description..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Filters Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Severity */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Severity
                </label>
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Any</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>

              {/* Exploited */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Exploitation Status
                </label>
                <select
                  value={exploited}
                  onChange={(e) => setExploited(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Any</option>
                  <option value="true">Exploited in Wild</option>
                  <option value="false">Not Exploited</option>
                </select>
              </div>

              {/* Vendor */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Vendor
                </label>
                <input
                  type="text"
                  value={vendor}
                  onChange={(e) => setVendor(e.target.value)}
                  placeholder="e.g., microsoft, apache"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Product */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Product
                </label>
                <input
                  type="text"
                  value={product}
                  onChange={(e) => setProduct(e.target.value)}
                  placeholder="e.g., windows, linux"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Min CVSS */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Min CVSS Score
                </label>
                <input
                  type="number"
                  value={minCvss}
                  onChange={(e) => setMinCvss(e.target.value)}
                  placeholder="0.0"
                  min="0"
                  max="10"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Max CVSS */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max CVSS Score
                </label>
                <input
                  type="number"
                  value={maxCvss}
                  onChange={(e) => setMaxCvss(e.target.value)}
                  placeholder="10.0"
                  min="0"
                  max="10"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Published After */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Published After
                </label>
                <input
                  type="date"
                  value={publishedAfter}
                  onChange={(e) => setPublishedAfter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Published Before */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Published Before
                </label>
                <input
                  type="date"
                  value={publishedBefore}
                  onChange={(e) => setPublishedBefore(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-4">
              <Button type="submit" disabled={loading}>
                <Search className="h-4 w-4 mr-2" />
                {loading ? "Searching..." : "Search"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={resetSearch}
                disabled={loading}
              >
                <X className="h-4 w-4 mr-2" />
                Reset
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Searching...</p>
        </div>
      )}

      {!loading && searched && results && (
        <>
          {/* Results Header */}
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {results.total === 0
                ? "No results found"
                : `Found ${results.total.toLocaleString()} result${results.total > 1 ? "s" : ""}`}
            </h2>
          </div>

          {/* Results List */}
          {results.total > 0 && (
            <div className="space-y-4">
              {results.items.map((vuln) => (
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
                            {vuln.title}
                          </h3>

                          {vuln.description && (
                            <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                              {vuln.description}
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
                            {vuln.published_at && (
                              <div className="flex items-center space-x-1">
                                <span className="font-medium">Published:</span>
                                <span>{formatDate(vuln.published_at)}</span>
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
          )}
        </>
      )}
    </div>
  );
}
