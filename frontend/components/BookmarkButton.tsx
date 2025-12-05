"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { Bookmark, BookmarkCheck } from "lucide-react";

interface BookmarkButtonProps {
  cveId: string;
  size?: "sm" | "md" | "lg";
}

export function BookmarkButton({ cveId, size = "md" }: BookmarkButtonProps) {
  const { token, isAuthenticated } = useAuth();
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [bookmarkId, setBookmarkId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-5 h-5",
    lg: "w-6 h-6",
  };

  const buttonSizeClasses = {
    sm: "p-1 text-xs",
    md: "p-2 text-sm",
    lg: "p-3 text-base",
  };

  useEffect(() => {
    if (isAuthenticated && token) {
      checkBookmark();
    }
  }, [isAuthenticated, token, cveId]);

  const checkBookmark = async () => {
    try {
      const response = await fetch(`/api/v1/bookmarks/check/${cveId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setIsBookmarked(data.is_bookmarked);
        setBookmarkId(data.bookmark_id);
      }
    } catch (error) {
      console.error("Failed to check bookmark:", error);
    }
  };

  const toggleBookmark = async () => {
    if (!isAuthenticated) {
      alert("Please sign in to bookmark CVEs");
      return;
    }

    setLoading(true);

    try {
      if (isBookmarked && bookmarkId) {
        // Remove bookmark
        const response = await fetch(`/api/v1/bookmarks/${bookmarkId}`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          setIsBookmarked(false);
          setBookmarkId(null);
        } else {
          throw new Error("Failed to remove bookmark");
        }
      } else {
        // Add bookmark
        const response = await fetch("/api/v1/bookmarks", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ cve_id: cveId }),
        });

        if (response.ok) {
          const data = await response.json();
          setIsBookmarked(true);
          setBookmarkId(data.id);
        } else {
          throw new Error("Failed to add bookmark");
        }
      }
    } catch (error) {
      console.error("Bookmark error:", error);
      alert("Failed to update bookmark. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <button
      onClick={toggleBookmark}
      disabled={loading}
      className={`${buttonSizeClasses[size]} flex items-center gap-2 rounded-lg border transition-colors ${
        isBookmarked
          ? "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700 text-yellow-700 dark:text-yellow-400 hover:bg-yellow-100 dark:hover:bg-yellow-900/30"
          : "bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
      } ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
      title={isBookmarked ? "Remove from bookmarks" : "Add to bookmarks"}
    >
      {isBookmarked ? (
        <BookmarkCheck className={sizeClasses[size]} />
      ) : (
        <Bookmark className={sizeClasses[size]} />
      )}
      <span className="hidden sm:inline">
        {isBookmarked ? "Bookmarked" : "Bookmark"}
      </span>
    </button>
  );
}
