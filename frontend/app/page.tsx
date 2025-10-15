import { fetchStats, fetchVulnerabilities } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tooltip } from "@/components/ui/tooltip";
import { AlertTriangle, Shield, TrendingUp, Clock } from "lucide-react";
import Link from "next/link";
import { formatDate, getSeverityBadgeColor } from "@/lib/utils";

export const revalidate = 60; // Revalidate every 60 seconds

export default async function HomePage() {
  const stats = await fetchStats();
  const exploitedVulns = await fetchVulnerabilities({
    exploited: true,
    page_size: 5,
    sort_by: "priority_score",
    sort_order: "desc",
  });

  const recentVulns = await fetchVulnerabilities({
    page_size: 5,
    sort_by: "published_at",
    sort_order: "desc",
  });

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4 py-8">
        <h1 className="text-4xl font-bold text-gray-900">
          Public Threat Intelligence Dashboard
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Democratizing threat intelligence. Track CVEs, exploited vulnerabilities,
          and security threats from public sources.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="flex items-center space-x-2">
              <CardTitle className="text-sm font-medium">
                Total Vulnerabilities
              </CardTitle>
              <Tooltip content="Total number of unique CVEs (Common Vulnerabilities and Exposures) tracked in our database from CISA, NVD, and other public sources." />
            </div>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.total_vulnerabilities.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Tracked CVEs from multiple sources
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="flex items-center space-x-2">
              <CardTitle className="text-sm font-medium">
                Exploited in Wild
              </CardTitle>
              <Tooltip content="Vulnerabilities that hackers are actively using right now to attack systems. These are confirmed by CISA and should be patched immediately." />
            </div>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {stats.exploited_vulnerabilities.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Actively exploited vulnerabilities
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Critical Severity
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {stats.critical_vulnerabilities.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Highest severity vulnerabilities
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Recent Updates
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.recent_updates.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Updated in last 7 days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Severity Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Severity Distribution</CardTitle>
          <CardDescription>
            Breakdown of vulnerabilities by severity level
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(stats.by_severity)
              .sort((a, b) => b[1] - a[1])
              .map(([severity, count]) => (
                <div key={severity} className="text-center">
                  <Badge className={getSeverityBadgeColor(severity)}>
                    {severity}
                  </Badge>
                  <div className="mt-2 text-2xl font-bold">{count}</div>
                  <div className="text-xs text-gray-500">
                    {((count / stats.total_vulnerabilities) * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Exploited Vulnerabilities */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <span>Top Exploited Vulnerabilities</span>
            </CardTitle>
            <CardDescription>
              Highest priority vulnerabilities exploited in the wild
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {exploitedVulns.items.map((vuln) => (
                <Link
                  key={vuln.cve_id}
                  href={`/vulnerabilities/${vuln.cve_id}`}
                  className="block p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-semibold text-blue-600">
                          {vuln.cve_id}
                        </span>
                        {vuln.severity && (
                          <Badge className={getSeverityBadgeColor(vuln.severity)}>
                            {vuln.severity}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                        {vuln.title}
                      </p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        {vuln.cvss_score && (
                          <span>CVSS: {vuln.cvss_score}</span>
                        )}
                        {vuln.published_at && (
                          <span>{formatDate(vuln.published_at)}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            <Link
              href="/vulnerabilities?exploited=true"
              className="block mt-4 text-center text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              View all exploited vulnerabilities →
            </Link>
          </CardContent>
        </Card>

        {/* Recent Vulnerabilities */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Clock className="h-5 w-5" />
              <span>Recently Published</span>
            </CardTitle>
            <CardDescription>
              Latest vulnerabilities added to the database
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentVulns.items.map((vuln) => (
                <Link
                  key={vuln.cve_id}
                  href={`/vulnerabilities/${vuln.cve_id}`}
                  className="block p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-semibold text-blue-600">
                          {vuln.cve_id}
                        </span>
                        {vuln.severity && (
                          <Badge className={getSeverityBadgeColor(vuln.severity)}>
                            {vuln.severity}
                          </Badge>
                        )}
                        {vuln.exploited_in_the_wild && (
                          <Badge className="bg-red-100 text-red-800">
                            Exploited
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                        {vuln.title}
                      </p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        {vuln.cvss_score && (
                          <span>CVSS: {vuln.cvss_score}</span>
                        )}
                        {vuln.published_at && (
                          <span>{formatDate(vuln.published_at)}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            <Link
              href="/vulnerabilities"
              className="block mt-4 text-center text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              View all vulnerabilities →
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
