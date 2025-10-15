import { fetchStats, fetchVulnerabilities } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Shield, TrendingUp, Clock, Calendar } from "lucide-react";
import Link from "next/link";
import { formatDate, getSeverityBadgeColor } from "@/lib/utils";

export const revalidate = 60; // Revalidate every 60 seconds

export default async function HomePage() {
  const stats = await fetchStats();
  
  // Fetch recent vulnerabilities for news feed
  const recentVulns = await fetchVulnerabilities({
    page_size: 20,
    sort_by: "published_at",
    sort_order: "desc",
  });

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4 py-8">
        <h1 className="text-4xl font-bold text-gray-900">
          Latest Security Threats
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Stay informed about the latest vulnerabilities and security threats
        </p>
      </div>

      {/* Quick Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-4 bg-white rounded-lg border">
          <div className="text-2xl font-bold text-gray-900">{stats.total_vulnerabilities.toLocaleString()}</div>
          <div className="text-sm text-gray-600">Total CVEs</div>
        </div>
        <div className="text-center p-4 bg-white rounded-lg border">
          <div className="text-2xl font-bold text-red-600">{stats.exploited_vulnerabilities.toLocaleString()}</div>
          <div className="text-sm text-gray-600">Exploited</div>
        </div>
        <div className="text-center p-4 bg-white rounded-lg border">
          <div className="text-2xl font-bold text-orange-600">{stats.critical_vulnerabilities.toLocaleString()}</div>
          <div className="text-sm text-gray-600">Critical</div>
        </div>
        <div className="text-center p-4 bg-white rounded-lg border">
          <div className="text-2xl font-bold text-blue-600">{stats.recent_updates.toLocaleString()}</div>
          <div className="text-sm text-gray-600">Last 7 Days</div>
        </div>
      </div>

      {/* News Feed - Recent Vulnerabilities */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Recent Vulnerabilities</h2>
          <Link href="/vulnerabilities" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View All →
          </Link>
        </div>

        <div className="space-y-4">
          {recentVulns.items.map((vuln: any) => {
            // Use LLM-generated content if available, otherwise fall back to original
            const displayTitle = vuln.simple_title || vuln.title;
            const displayDescription = vuln.simple_description || vuln.description;
            
            return (
              <Link
                key={vuln.cve_id}
                href={`/vulnerabilities/${vuln.cve_id}`}
                className="block"
              >
                <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                  <CardContent className="p-6">
                    {/* Article Title */}
                    <h3 className="text-xl font-bold text-gray-900 mb-3 hover:text-blue-600 transition-colors">
                      {displayTitle}
                    </h3>
                    
                    {/* Article Description */}
                    <p className="text-gray-700 mb-4 line-clamp-3">
                      {displayDescription}
                    </p>
                    
                    {/* Metadata Row */}
                    <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
                      {/* CVE ID */}
                      <span className="font-mono font-semibold text-blue-600">
                        {vuln.cve_id}
                      </span>
                      
                      {/* Severity Badge */}
                      {vuln.severity && (
                        <Badge className={getSeverityBadgeColor(vuln.severity)}>
                          {vuln.severity}
                        </Badge>
                      )}
                      
                      {/* Exploited Badge */}
                      {vuln.exploited_in_the_wild && (
                        <Badge className="bg-red-100 text-red-800 border-red-300">
                          <AlertTriangle className="h-3 w-3 mr-1" />
                          Exploited
                        </Badge>
                      )}
                      
                      {/* CVSS Score */}
                      {vuln.cvss_score && (
                        <span className="flex items-center gap-1">
                          <Shield className="h-3 w-3" />
                          CVSS {vuln.cvss_score}
                        </span>
                      )}
                      
                      {/* Date */}
                      {vuln.published_at && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(vuln.published_at)}
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
