export interface UserInfo {
  id: number;
  username: string;
  role: string;
}

export interface Comment {
  id: number;
  content: string;
  cve_id: string;
  user_id: number;
  parent_id: number | null;
  created_at: string;
  updated_at: string;
  is_edited: boolean;
  is_deleted: boolean;
  upvotes: number;
  downvotes: number;
  user: UserInfo;
  reply_count: number;
  user_vote: number | null; // 1 for upvote, -1 for downvote, null for no vote
}

export interface CommentListResponse {
  comments: Comment[];
  total: number;
  page: number;
  page_size: number;
}
