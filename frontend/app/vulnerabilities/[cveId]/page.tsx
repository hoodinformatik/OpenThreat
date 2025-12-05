import { notFound } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Shield,
  AlertTriangle,
  Calendar,
  ExternalLink,
  ArrowLeft,
  TrendingUp,
  Package,
  Building2,
  Bug,
} from "lucide-react";
import { formatDate, getSeverityBadgeColor } from "@/lib/utils";
import type { VulnerabilityDetail } from "@/lib/api";
import { Tooltip } from "@/components/ui/tooltip";
import {
  explainSeverity,
  explainExploitation,
  explainCVSS,
  explainCWE,
  explainPriorityScore,
  generateActionPlan,
  explainCVE,
} from "@/lib/explanations";
import { VulnerabilityComments } from "@/components/VulnerabilityComments";
import { BookmarkButton } from "@/components/BookmarkButton";

// API URL - use internal Docker network URL for SSR, public URL for client
const getApiUrl = () => {
  // Server-side (SSR): use internal Docker network URL
  if (typeof window === 'undefined') {
    return process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
  }
  // Client-side: use public URL
  return process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
};

async function fetchVulnerability(cveId: string): Promise<VulnerabilityDetail> {
  const apiUrl = getApiUrl();
  const res = await fetch(`${apiUrl}/api/v1/vulnerabilities/${cveId}`, {
    next: { revalidate: 3600 }, // Cache for 1 hour - CVE data rarely changes
    cache: 'force-cache',
  });

  if (!res.ok) {
    notFound();
  }

  return res.json();
}

export default async function VulnerabilityDetailPage({
  params,
}: {
  params: Promise<{ cveId: string }>;
}) {
  const { cveId } = await params;
  const vuln = await fetchVulnerability(cveId);

  return (
    <div className="space-y-6">
      {/* Back Button and Bookmark */}
      <div className="flex items-center justify-between">
        <Link href="/vulnerabilities">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to List
          </Button>
        </Link>
        <BookmarkButton cveId={cveId} size="md" />
      </div>

      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h1 className="text-3xl font-bold font-mono text-gray-900 dark:text-white">
                {vuln.cve_id}
              </h1>
              <Tooltip content={explainCVE()} />
              {vuln.severity && (
                <div className="inline-flex items-center space-x-1">
                  <Badge className={getSeverityBadgeColor(vuln.severity)}>
                    {vuln.severity}
                  </Badge>
                  <Tooltip content={`${explainSeverity(vuln.severity).simple} - ${explainSeverity(vuln.severity).whatItMeans}`} />
                </div>
              )}
              {vuln.exploited_in_the_wild && (
                <div className="inline-flex items-center space-x-1">
                  <Badge className="bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400 border-red-300 dark:border-red-700">
                    <AlertTriangle className="h-4 w-4 mr-1" />
                    Exploited in Wild
                  </Badge>
                  <Tooltip content={`${explainExploitation(vuln.exploited_in_the_wild).simple} - ${explainExploitation(vuln.exploited_in_the_wild).whatItMeans}`} />
                </div>
              )}
            </div>
            <h2 className="text-xl text-gray-700 dark:text-gray-300">{vuln.title}</h2>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {vuln.cvss_score && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="flex items-center justify-center space-x-2 mb-1">
                    <p className="text-sm text-gray-600 dark:text-gray-400">CVSS Score</p>
                    <Tooltip content={explainCVSS(vuln.cvss_score)} />
                  </div>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white">
                    {vuln.cvss_score}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Base Score (0-10)</p>
                </div>
              </CardContent>
            </Card>
          )}

          {vuln.priority_score && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="flex items-center justify-center space-x-2 mb-1">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Priority Score</p>
                    <Tooltip content={explainPriorityScore(vuln.priority_score)} />
                  </div>
                  <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                    {vuln.priority_score.toFixed(2)}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {(vuln.priority_score * 100).toFixed(0)}% priority
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {vuln.published_at && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Published</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {formatDate(vuln.published_at)}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {new Date(vuln.published_at).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                    })}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {vuln.cisa_due_date && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">CISA Due Date</p>
                  <p className="text-lg font-semibold text-red-600 dark:text-red-400">
                    {formatDate(vuln.cisa_due_date)}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Action Required</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>


      {/* Action Plan */}
      {(() => {
        const actionPlan = generateActionPlan(vuln);
        return (
          <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
            <CardHeader>
              <CardTitle className="text-lg">
                {actionPlan.priority} - Recommended Action Plan
              </CardTitle>
              <CardDescription>Timeline: {actionPlan.timeline}</CardDescription>
            </CardHeader>
            <CardContent>
              <ol className="space-y-2">
                {actionPlan.steps.map((step, idx) => (
                  <li key={idx} className="text-sm text-gray-700 dark:text-gray-300">
                    {step}
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        );
      })()}

      {/* Description */}
      {vuln.description && (
        <Card>
          <CardHeader>
            <CardTitle>Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{vuln.description}</p>
          </CardContent>
        </Card>
      )}

      {/* CVSS Vector */}
      {vuln.cvss_vector && (
        <Card>
          <CardHeader>
            <CardTitle>CVSS Vector</CardTitle>
            <CardDescription>Common Vulnerability Scoring System</CardDescription>
          </CardHeader>
          <CardContent>
            <code className="block bg-gray-100 dark:bg-gray-700 p-3 rounded text-sm font-mono text-gray-900 dark:text-gray-100">
              {vuln.cvss_vector}
            </code>
          </CardContent>
        </Card>
      )}

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CWE IDs */}
        {vuln.cwe_ids && vuln.cwe_ids.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bug className="h-5 w-5" />
                <span>CWE IDs</span>
              </CardTitle>
              <CardDescription>Common Weakness Enumeration</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {vuln.cwe_ids.map((cwe) => (
                  <div key={cwe} className="flex items-start space-x-2">
                    <Badge variant="outline" className="mt-0.5">
                      {cwe}
                    </Badge>
                    <p className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                      {explainCWE(cwe)}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Sources */}
        {vuln.sources && vuln.sources.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5" />
                <span>Data Sources</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {vuln.sources.map((source) => (
                  <Badge key={source} variant="secondary">
                    {source}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Vendors */}
      {vuln.vendors && vuln.vendors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Building2 className="h-5 w-5" />
              <span>Affected Vendors</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {vuln.vendors.map((vendor) => (
                <Badge key={vendor} variant="outline" className="capitalize">
                  {vendor}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Products */}
      {vuln.products && vuln.products.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Package className="h-5 w-5" />
              <span>Affected Products</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {vuln.products.map((product) => (
                <Badge key={product} variant="outline" className="capitalize">
                  {product}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Affected Products (CPE format) */}
      {vuln.affected_products && vuln.affected_products.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Affected Products (CPE)</CardTitle>
            <CardDescription>Common Platform Enumeration</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {vuln.affected_products.map((product, idx) => (
                <code
                  key={idx}
                  className="block bg-gray-50 dark:bg-gray-700 p-2 rounded text-xs font-mono text-gray-700 dark:text-gray-300"
                >
                  {product}
                </code>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* References */}
      {vuln.references && vuln.references.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>References</CardTitle>
            <CardDescription>
              External links and additional information
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {vuln.references.map((ref, idx) => (
                <div key={idx} className="flex items-start space-x-3">
                  <ExternalLink className="h-4 w-4 text-gray-400 dark:text-gray-500 mt-1 flex-shrink-0" />
                  <div className="flex-1">
                    <a
                      href={ref.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:underline break-all"
                    >
                      {ref.url}
                    </a>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {ref.tags && ref.tags.length > 0 && ref.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="font-medium text-gray-600 dark:text-gray-400">CVE ID</dt>
              <dd className="mt-1 font-mono text-gray-900 dark:text-white">{vuln.cve_id}</dd>
            </div>
            {vuln.published_at && (
              <div>
                <dt className="font-medium text-gray-600 dark:text-gray-400">Published</dt>
                <dd className="mt-1 text-gray-900 dark:text-white">{formatDate(vuln.published_at)}</dd>
              </div>
            )}
            {vuln.modified_at && (
              <div>
                <dt className="font-medium text-gray-600 dark:text-gray-400">Last Modified</dt>
                <dd className="mt-1 text-gray-900 dark:text-white">{formatDate(vuln.modified_at)}</dd>
              </div>
            )}
            {vuln.created_at && (
              <div>
                <dt className="font-medium text-gray-600 dark:text-gray-400">Added to Database</dt>
                <dd className="mt-1 text-gray-900 dark:text-white">{formatDate(vuln.created_at)}</dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      {/* Comments Section */}
      <VulnerabilityComments cveId={cveId} />
    </div>
  );
}
