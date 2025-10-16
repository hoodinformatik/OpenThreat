const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';

export interface Vulnerability {
  cve_id: string;
  title: string;
  description?: string;
  simple_title?: string;
  simple_description?: string;
  llm_processed?: boolean;
  cvss_score?: number;
  cvss_vector?: string;
  severity?: string;
  exploited_in_the_wild: boolean;
  priority_score?: number;
  published_at?: string;
  modified_at?: string;
  sources?: string[];
}

export interface VulnerabilityDetail extends Vulnerability {
  id: number;
  cisa_due_date?: string;
  cwe_ids?: string[];
  affected_products?: string[];
  vendors?: string[];
  products?: string[];
  references?: Array<{
    url: string;
    type: string;
    tags?: string[];
  }>;
  source_tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: T[];
}

export interface Stats {
  total_vulnerabilities: number;
  exploited_vulnerabilities: number;
  critical_vulnerabilities: number;
  high_vulnerabilities: number;
  by_severity: Record<string, number>;
  recent_updates: number;
  last_update?: string;
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_URL}/api/v1/stats`, {
    next: { revalidate: 60 } // Cache for 1 minute
  });
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchVulnerabilities(params: {
  page?: number;
  page_size?: number;
  severity?: string;
  exploited?: boolean;
  sort_by?: string;
  sort_order?: string;
}): Promise<PaginatedResponse<Vulnerability>> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });

  const res = await fetch(`${API_URL}/api/v1/vulnerabilities?${searchParams}`, {
    next: { revalidate: 60 }
  });
  if (!res.ok) throw new Error('Failed to fetch vulnerabilities');
  return res.json();
}

export async function fetchVulnerability(cveId: string): Promise<VulnerabilityDetail> {
  const res = await fetch(`${API_URL}/api/v1/vulnerabilities/${cveId}`, {
    next: { revalidate: 60 }
  });
  if (!res.ok) throw new Error('Failed to fetch vulnerability');
  return res.json();
}

export async function searchVulnerabilities(params: {
  q?: string;
  severity?: string;
  exploited?: boolean;
  vendor?: string;
  product?: string;
  min_cvss?: number;
  max_cvss?: number;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<Vulnerability>> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });

  const res = await fetch(`${API_URL}/api/v1/search?${searchParams}`, {
    cache: 'no-store' // Don't cache search results
  });
  if (!res.ok) throw new Error('Failed to search vulnerabilities');
  return res.json();
}

export async function fetchTopVendors(limit: number = 20) {
  const res = await fetch(`${API_URL}/api/v1/stats/top-vendors?limit=${limit}`, {
    next: { revalidate: 300 } // Cache for 5 minutes
  });
  if (!res.ok) throw new Error('Failed to fetch top vendors');
  return res.json();
}

export async function fetchSeverityDistribution() {
  const res = await fetch(`${API_URL}/api/v1/stats/severity-distribution`, {
    next: { revalidate: 300 }
  });
  if (!res.ok) throw new Error('Failed to fetch severity distribution');
  return res.json();
}
