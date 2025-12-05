"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Comment } from "@/types/comment";

interface CommentFormProps {
  cveId: string;
  parentId?: number;
  onCommentAdded: (comment: Comment) => void;
  onCancel?: () => void;
  placeholder?: string;
}

export function CommentForm({
  cveId,
  parentId,
  onCommentAdded,
  onCancel,
  placeholder = "Write a comment...",
}: CommentFormProps) {
  const { token, isAuthenticated } = useAuth();
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isAuthenticated || !token) {
      setError("Please sign in to comment");
      return;
    }

    if (!content.trim()) {
      setError("Comment cannot be empty");
      return;
    }

    if (content.length > 5000) {
      setError("Comment is too long (max 5000 characters)");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const response = await fetch(`/api/v1/vulnerabilities/${cveId}/comments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          content: content.trim(),
          parent_id: parentId || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to post comment");
      }

      const newComment = await response.json();
      onCommentAdded(newComment);
      setContent("");

      if (onCancel) {
        onCancel();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={placeholder}
          rows={4}
          maxLength={5000}
          disabled={submitting}
          className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed resize-none"
        />
        <div className="flex justify-between items-center mt-1">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {content.length} / 5000 characters
          </span>
          {content.length > 4500 && (
            <span className="text-sm text-orange-600 dark:text-orange-400">
              {5000 - content.length} characters remaining
            </span>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting || !content.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? "Posting..." : parentId ? "Reply" : "Post Comment"}
        </button>

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Cancel
          </button>
        )}
      </div>

      <div className="text-xs text-gray-500 dark:text-gray-400">
        <p>💡 Tips:</p>
        <ul className="list-disc list-inside mt-1 space-y-1">
          <li>Only plain text is allowed (no HTML or scripts)</li>
          <li>Be respectful and constructive</li>
          <li>You can edit or delete your comment later</li>
        </ul>
      </div>
    </form>
  );
}
