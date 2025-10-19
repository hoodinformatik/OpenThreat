"use client";

import { Comment } from "@/types/comment";
import { CommentItem } from "./CommentItem";

interface CommentListProps {
  comments: Comment[];
  cveId: string;
  onCommentUpdated: (comment: Comment) => void;
  onCommentDeleted: (commentId: number) => void;
  onVote: (commentId: number, voteType: 1 | -1) => void;
}

export function CommentList({
  comments,
  cveId,
  onCommentUpdated,
  onCommentDeleted,
  onVote,
}: CommentListProps) {
  return (
    <div className="space-y-4">
      {comments.map((comment) => (
        <CommentItem
          key={comment.id}
          comment={comment}
          cveId={cveId}
          onCommentUpdated={onCommentUpdated}
          onCommentDeleted={onCommentDeleted}
          onVote={onVote}
        />
      ))}
    </div>
  );
}
