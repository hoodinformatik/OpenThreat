"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Comment } from "@/types/comment";
import { CommentForm } from "./CommentForm";
import { formatDistanceToNow } from "date-fns";
import { ChevronUp, ChevronDown, MessageSquare, Edit2, Trash2, MoreVertical } from "lucide-react";

interface CommentItemProps {
  comment: Comment;
  cveId: string;
  onCommentUpdated: (comment: Comment) => void;
  onCommentDeleted: (commentId: number) => void;
  onVote: (commentId: number, voteType: 1 | -1) => void;
  depth?: number;
}

export function CommentItem({
  comment,
  cveId,
  onCommentUpdated,
  onCommentDeleted,
  onVote,
  depth = 0,
}: CommentItemProps) {
  const { user, token, isAuthenticated } = useAuth();
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [showReplies, setShowReplies] = useState(false);
  const [replies, setReplies] = useState<Comment[]>([]);
  const [loadingReplies, setLoadingReplies] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [showMenu, setShowMenu] = useState(false);

  const isAuthor = user?.id === comment.user_id;
  const isAdmin = user?.role === "admin";
  const canEdit = isAuthor;
  const canDelete = isAuthor || isAdmin;

  const score = comment.upvotes - comment.downvotes;

  const loadReplies = async () => {
    if (replies.length > 0) {
      setShowReplies(!showReplies);
      return;
    }

    try {
      setLoadingReplies(true);
      const response = await fetch(
        `/api/v1/comments/${comment.id}/replies?page=1&page_size=50`,
        {
          headers: token
            ? { Authorization: `Bearer ${token}` }
            : {},
        }
      );

      if (!response.ok) {
        throw new Error("Failed to load replies");
      }

      const data = await response.json();
      setReplies(data.comments);
      setShowReplies(true);
    } catch (err) {
      console.error("Failed to load replies:", err);
      alert("Failed to load replies. Please try again.");
    } finally {
      setLoadingReplies(false);
    }
  };

  const handleEdit = async () => {
    if (!editContent.trim()) {
      alert("Comment cannot be empty");
      return;
    }

    try {
      const response = await fetch(`/api/v1/comments/${comment.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ content: editContent.trim() }),
      });

      if (!response.ok) {
        throw new Error("Failed to update comment");
      }

      const updatedComment = await response.json();
      onCommentUpdated(updatedComment);
      setEditing(false);
    } catch (err) {
      console.error("Edit error:", err);
      alert("Failed to update comment. Please try again.");
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this comment?")) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/comments/${comment.id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to delete comment");
      }

      onCommentDeleted(comment.id);
    } catch (err) {
      console.error("Delete error:", err);
      alert("Failed to delete comment. Please try again.");
    }
  };

  const handleReplyAdded = (newReply: Comment) => {
    setReplies([...replies, newReply]);
    setShowReplyForm(false);
    setShowReplies(true);
  };

  if (comment.is_deleted) {
    return (
      <div className={`${depth > 0 ? "ml-8 pl-4 border-l-2 border-gray-200" : ""}`}>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-gray-500 italic">[Comment deleted]</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${depth > 0 ? "ml-8 pl-4 border-l-2 border-gray-200" : ""}`}>
      <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
              {comment.user.username.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-900">
                  {comment.user.username}
                </span>
                {comment.user.role === "admin" && (
                  <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">
                    Admin
                  </span>
                )}
                {comment.user.role === "analyst" && (
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                    Analyst
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span>
                  {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}
                </span>
                {comment.is_edited && <span>• edited</span>}
              </div>
            </div>
          </div>

          {(canEdit || canDelete) && (
            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <MoreVertical className="w-4 h-4 text-gray-500" />
              </button>

              {showMenu && (
                <div className="absolute right-0 mt-1 w-32 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                  {canEdit && !editing && (
                    <button
                      onClick={() => {
                        setEditing(true);
                        setShowMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                    >
                      <Edit2 className="w-3 h-3" />
                      Edit
                    </button>
                  )}
                  {canDelete && (
                    <button
                      onClick={() => {
                        handleDelete();
                        setShowMenu(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                    >
                      <Trash2 className="w-3 h-3" />
                      Delete
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Content */}
        {editing ? (
          <div className="mb-3 space-y-2">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              rows={4}
              maxLength={5000}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <div className="flex gap-2">
              <button
                onClick={handleEdit}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
              >
                Save
              </button>
              <button
                onClick={() => {
                  setEditing(false);
                  setEditContent(comment.content);
                }}
                className="px-3 py-1 border border-gray-300 text-sm rounded hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="mb-3">
            <p className="text-gray-800 whitespace-pre-wrap break-words">
              {comment.content}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-4 text-sm">
          {/* Voting */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => onVote(comment.id, 1)}
              disabled={!isAuthenticated}
              className={`p-1 rounded hover:bg-gray-100 transition-colors ${
                comment.user_vote === 1 ? "text-blue-600" : "text-gray-500"
              } ${!isAuthenticated ? "cursor-not-allowed opacity-50" : ""}`}
              title={isAuthenticated ? "Upvote" : "Sign in to vote"}
            >
              <ChevronUp className="w-5 h-5" />
            </button>
            <span
              className={`font-semibold min-w-[2rem] text-center ${
                score > 0 ? "text-blue-600" : score < 0 ? "text-red-600" : "text-gray-600"
              }`}
            >
              {score}
            </span>
            <button
              onClick={() => onVote(comment.id, -1)}
              disabled={!isAuthenticated}
              className={`p-1 rounded hover:bg-gray-100 transition-colors ${
                comment.user_vote === -1 ? "text-red-600" : "text-gray-500"
              } ${!isAuthenticated ? "cursor-not-allowed opacity-50" : ""}`}
              title={isAuthenticated ? "Downvote" : "Sign in to vote"}
            >
              <ChevronDown className="w-5 h-5" />
            </button>
          </div>

          {/* Reply button */}
          {isAuthenticated && depth < 3 && (
            <button
              onClick={() => setShowReplyForm(!showReplyForm)}
              className="flex items-center gap-1 text-gray-600 hover:text-blue-600 transition-colors"
            >
              <MessageSquare className="w-4 h-4" />
              Reply
            </button>
          )}

          {/* Show replies button */}
          {comment.reply_count > 0 && (
            <button
              onClick={loadReplies}
              disabled={loadingReplies}
              className="flex items-center gap-1 text-gray-600 hover:text-blue-600 transition-colors"
            >
              <MessageSquare className="w-4 h-4" />
              {loadingReplies ? "Loading..." : `${comment.reply_count} ${comment.reply_count === 1 ? "reply" : "replies"}`}
            </button>
          )}
        </div>

        {/* Reply form */}
        {showReplyForm && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <CommentForm
              cveId={cveId}
              parentId={comment.id}
              onCommentAdded={handleReplyAdded}
              onCancel={() => setShowReplyForm(false)}
              placeholder="Write a reply..."
            />
          </div>
        )}
      </div>

      {/* Nested replies */}
      {showReplies && replies.length > 0 && (
        <div className="mt-2 space-y-2">
          {replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              cveId={cveId}
              onCommentUpdated={onCommentUpdated}
              onCommentDeleted={onCommentDeleted}
              onVote={onVote}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}
