"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { CommentForm } from "./CommentForm";
import { CommentList } from "./CommentList";
import { Comment } from "@/types/comment";

interface CommentSectionProps {
  cveId: string;
}

export function CommentSection({ cveId }: CommentSectionProps) {
  const { user, token, isAuthenticated } = useAuth();
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [sortBy, setSortBy] = useState<"created_at" | "upvotes">("created_at");

  const pageSize = 20;

  const fetchComments = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `/api/v1/vulnerabilities/${cveId}/comments?page=${page}&page_size=${pageSize}&sort_by=${sortBy}&order=desc`,
        {
          headers: token
            ? { Authorization: `Bearer ${token}` }
            : {},
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch comments");
      }

      const data = await response.json();
      setComments(data.comments);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, [cveId, page, sortBy]);

  const handleCommentAdded = (newComment: Comment) => {
    setComments([newComment, ...comments]);
    setTotal(total + 1);
  };

  const handleCommentUpdated = (updatedComment: Comment) => {
    setComments(
      comments.map((c) => (c.id === updatedComment.id ? updatedComment : c))
    );
  };

  const handleCommentDeleted = (commentId: number) => {
    setComments(comments.filter((c) => c.id !== commentId));
    setTotal(total - 1);
  };

  const handleVote = async (commentId: number, voteType: 1 | -1) => {
    if (!isAuthenticated || !token) {
      alert("Please sign in to vote");
      return;
    }

    try {
      const response = await fetch(`/api/v1/comments/${commentId}/vote`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ vote_type: voteType }),
      });

      if (!response.ok) {
        throw new Error("Failed to vote");
      }

      const updatedComment = await response.json();
      handleCommentUpdated(updatedComment);
    } catch (err) {
      console.error("Vote error:", err);
      alert("Failed to vote. Please try again.");
    }
  };

  return (
    <div className="mt-8 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">
          Comments ({total})
        </h2>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "created_at" | "upvotes")}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="created_at">Newest First</option>
          <option value="upvotes">Most Upvoted</option>
        </select>
      </div>

      {isAuthenticated ? (
        <CommentForm
          cveId={cveId}
          onCommentAdded={handleCommentAdded}
        />
      ) : (
        <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            Please{" "}
            <a href="/auth" className="text-blue-600 dark:text-blue-400 hover:underline">
              sign in
            </a>{" "}
            to comment
          </p>
        </div>
      )}

      {loading && page === 1 ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-400"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Loading comments...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">{error}</p>
          <button
            onClick={fetchComments}
            className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
          >
            Try again
          </button>
        </div>
      ) : comments.length === 0 ? (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No comments yet. Be the first to comment!
        </div>
      ) : (
        <>
          <CommentList
            comments={comments}
            cveId={cveId}
            onCommentUpdated={handleCommentUpdated}
            onCommentDeleted={handleCommentDeleted}
            onVote={handleVote}
          />

          {total > pageSize && (
            <div className="flex justify-center gap-2 mt-6">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-gray-700 dark:text-gray-300">
                Page {page} of {Math.ceil(total / pageSize)}
              </span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(total / pageSize)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
