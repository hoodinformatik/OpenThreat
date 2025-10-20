export interface Bookmark {
  id: number;
  cve_id: string;
  user_id: number;
  created_at: string;
  notes: string | null;
  vulnerability: {
    cve_id: string;
    description: string;
    severity: string | null;
    cvss_score: number | null;
    published_date: string | null;
    is_exploited: boolean;
  } | null;
}

export interface BookmarkListResponse {
  bookmarks: Bookmark[];
  total: number;
  page: number;
  page_size: number;
}
