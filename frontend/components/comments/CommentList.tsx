"use client";

import { Comment } from "@/types/comment";
import { CommentItem } from "./CommentItem";

interface CommentListProps {
  comments: Comment[];
  onCommentUpdated: (comment: Comment) => void;
  onCommentDeleted: (commentId: number) => void;
}

export function CommentList({
  comments,
  onCommentUpdated,
  onCommentDeleted,
}: CommentListProps) {
  return (
    <div className="space-y-4">
      {comments.map((comment) => (
        <CommentItem
          key={comment.id}
          comment={comment}
          onCommentUpdated={onCommentUpdated}
          onCommentDeleted={onCommentDeleted}
        />
      ))}
    </div>
  );
}
