export interface UserInfo {
  id: number;
  username: string;
  role: string;
}

export interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  comment_id: number | null;
  cve_id: string | null;
  actor: UserInfo | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
}
