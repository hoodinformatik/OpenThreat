"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Bookmark as BookmarkType, BookmarkListResponse } from "@/types/bookmark";
import { formatDistanceToNow } from "date-fns";
import { Bookmark, Trash2, AlertTriangle, Shield, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function BookmarksPage() {
  const { token, isAuthenticated } = useAuth();
  const [bookmarks, setBookmarks] = useState<BookmarkType[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const pageSize = 20;

  useEffect(() => {
    if (isAuthenticated && token) {
      fetchBookmarks();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated, token, page]);

  const fetchBookmarks = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/v1/bookmarks?page=${page}&page_size=${pageSize}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data: BookmarkListResponse = await response.json();
        setBookmarks(data.bookmarks);
        setTotal(data.total);
      }
    } catch (error) {
      console.error("Failed to fetch bookmarks:", error);
    } finally {
      setLoading(false);
    }
  };

  const removeBookmark = async (bookmarkId: number) => {
    if (!confirm("Remove this bookmark?")) return;

    try {
      const response = await fetch(`/api/v1/bookmarks/${bookmarkId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setBookmarks(bookmarks.filter((b) => b.id !== bookmarkId));
        setTotal(total - 1);
      }
    } catch (error) {
      console.error("Failed to remove bookmark:", error);
      alert("Failed to remove bookmark. Please try again.");
    }
  };

  const getSeverityColor = (severity: string | null) => {
    if (!severity) return "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300";
    switch (severity.toUpperCase()) {
      case "CRITICAL":
        return "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400";
      case "HIGH":
        return "bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400";
      case "MEDIUM":
        return "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400";
      case "LOW":
        return "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400";
      default:
        return "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300";
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto text-center">
          <Bookmark className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Sign in to view bookmarks
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            You need to be signed in to see your bookmarked CVEs.
          </p>
          <Link
            href="/auth"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                <Bookmark className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
                My Bookmarks
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {total > 0
                  ? `${total} bookmarked CVE${total === 1 ? "" : "s"}`
                  : "No bookmarks yet"}
              </p>
            </div>
          </div>
        </div>

        {/* Bookmarks List */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : bookmarks.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-12 text-center">
            <Bookmark className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              No bookmarks yet
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Start bookmarking CVEs to track them here
            </p>
            <Link
              href="/"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Browse CVEs
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {bookmarks.map((bookmark) => (
              <div
                key={bookmark.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    {/* CVE ID and Severity */}
                    <div className="flex items-center gap-3 mb-2">
                      <Link
                        href={`/vulnerabilities/${bookmark.cve_id}`}
                        className="text-xl font-bold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                      >
                        {bookmark.cve_id}
                      </Link>
                      {bookmark.vulnerability?.severity && (
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded ${getSeverityColor(
                            bookmark.vulnerability.severity
                          )}`}
                        >
                          {bookmark.vulnerability.severity}
                        </span>
                      )}
                      {bookmark.vulnerability?.is_exploited && (
                        <span className="flex items-center gap-1 px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs font-semibold rounded">
                          <AlertTriangle className="w-3 h-3" />
                          EXPLOITED
                        </span>
                      )}
                    </div>

                    {/* Description */}
                    {bookmark.vulnerability?.description && (
                      <p className="text-gray-700 dark:text-gray-300 mb-3 line-clamp-2">
                        {bookmark.vulnerability.description}
                      </p>
                    )}

                    {/* Metadata */}
                    <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                      {bookmark.vulnerability?.cvss_score && (
                        <div className="flex items-center gap-1">
                          <Shield className="w-4 h-4" />
                          <span>CVSS: {bookmark.vulnerability.cvss_score}</span>
                        </div>
                      )}
                      <span>
                        Bookmarked{" "}
                        {formatDistanceToNow(new Date(bookmark.created_at), {
                          addSuffix: true,
                        })}
                      </span>
                    </div>

                    {/* Notes */}
                    {bookmark.notes && (
                      <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded">
                        <p className="text-sm text-gray-700 dark:text-gray-300">{bookmark.notes}</p>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <button
                    onClick={() => removeBookmark(bookmark.id)}
                    className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                    title="Remove bookmark"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {total > pageSize && (
          <div className="flex items-center justify-between mt-6 px-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Showing {(page - 1) * pageSize + 1} to{" "}
              {Math.min(page * pageSize, total)} of {total} bookmarks
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(total / pageSize)}
                className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
