import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Shield,
  AlertTriangle,
  ExternalLink,
  ArrowLeft,
  Package,
  Building2,
  Bug,
} from "lucide-react";
import { formatDate, getSeverityBadgeColor, getSeverityAccentColor } from "@/lib/utils";
import type { VulnerabilityDetail } from "@/lib/api";
import { Tooltip } from "@/components/ui/tooltip";
import {
  explainSeverity,
  explainExploitation,
  explainCVSS,
  explainPriorityScore,
  explainCWE,
  generateActionPlan,
  explainCVE,
} from "@/lib/explanations";
import { VulnerabilityComments } from "@/components/VulnerabilityComments";
import { notFound } from "next/navigation";

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
  const displayTitle = vuln.simple_title || vuln.title;
  const actionPlan = generateActionPlan(vuln);

  const hasTechnicalDetails =
    vuln.cvss_vector ||
    (vuln.cwe_ids && vuln.cwe_ids.length > 0) ||
    (vuln.vendors && vuln.vendors.length > 0) ||
    (vuln.products && vuln.products.length > 0) ||
    (vuln.affected_products && vuln.affected_products.length > 0);

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link href="/">
        <Button variant="outline" size="sm">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>
      </Link>

      {/* Header / Summary */}
      <Card className={`border-l-4 ${getSeverityAccentColor(vuln.severity)}`}>
        <CardContent className="pt-6 space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-2xl font-bold font-mono text-gray-900 dark:text-white">
              {vuln.cve_id}
            </span>
            <Tooltip content={explainCVE()} />
            {vuln.severity && (
              <div className="inline-flex items-center gap-1">
                <Badge className={getSeverityBadgeColor(vuln.severity)}>
                  {vuln.severity}
                </Badge>
                <Tooltip content={`${explainSeverity(vuln.severity).simple} - ${explainSeverity(vuln.severity).whatItMeans}`} />
              </div>
            )}
            {vuln.exploited_in_the_wild && (
              <div className="inline-flex items-center gap-1">
                <Badge className="bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400 border-red-300 dark:border-red-700">
                  <AlertTriangle className="h-4 w-4 mr-1" />
                  Exploited in Wild
                </Badge>
                <Tooltip content={`${explainExploitation(vuln.exploited_in_the_wild).simple} - ${explainExploitation(vuln.exploited_in_the_wild).whatItMeans}`} />
              </div>
            )}
          </div>

          <h1 className="text-xl md:text-2xl font-semibold text-gray-900 dark:text-white">
            {displayTitle}
          </h1>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2 border-t border-gray-200 dark:border-gray-700">
            {vuln.cvss_score != null && (
              <div>
                <div className="flex items-center gap-1.5">
                  <p className="text-sm text-gray-600 dark:text-gray-400">CVSS Score</p>
                  <Tooltip content={explainCVSS(vuln.cvss_score)} />
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{vuln.cvss_score}</p>
              </div>
            )}

            {vuln.priority_score != null && (
              <div>
                <div className="flex items-center gap-1.5">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Priority</p>
                  <Tooltip content={explainPriorityScore(vuln.priority_score)} />
                </div>
                <p className="text-2xl font-bold text-primary">
                  {(vuln.priority_score * 100).toFixed(0)}%
                </p>
              </div>
            )}

            {vuln.published_at && (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Published</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {formatDate(vuln.published_at)}
                </p>
              </div>
            )}

            {vuln.cisa_due_date && (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">CISA Due Date</p>
                <p className="text-lg font-semibold text-red-600 dark:text-red-400">
                  {formatDate(vuln.cisa_due_date)}
                </p>
              </div>
            )}

            {!vuln.published_at && vuln.modified_at && (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Last Modified</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {formatDate(vuln.modified_at)}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Action Plan */}
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

      {/* Technical Details */}
      {hasTechnicalDetails && (
        <Card>
          <CardHeader>
            <CardTitle>Technical Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {vuln.cvss_vector && (
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                  CVSS Vector
                </h3>
                <code className="block bg-gray-100 dark:bg-gray-700 p-3 rounded text-sm font-mono text-gray-900 dark:text-gray-100">
                  {vuln.cvss_vector}
                </code>
              </div>
            )}

            {vuln.cwe_ids && vuln.cwe_ids.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                  <Bug className="h-4 w-4" />
                  Weakness Types (CWE)
                </h3>
                <div className="space-y-2">
                  {vuln.cwe_ids.map((cwe) => (
                    <div key={cwe} className="flex items-start gap-2">
                      <Badge variant="outline" className="mt-0.5">{cwe}</Badge>
                      <p className="text-sm text-gray-700 dark:text-gray-300 flex-1">{explainCWE(cwe)}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {vuln.vendors && vuln.vendors.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  Affected Vendors
                </h3>
                <div className="flex flex-wrap gap-2">
                  {vuln.vendors.map((vendor) => (
                    <Badge key={vendor} variant="outline" className="capitalize">{vendor}</Badge>
                  ))}
                </div>
              </div>
            )}

            {vuln.products && vuln.products.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Affected Products
                </h3>
                <div className="flex flex-wrap gap-2">
                  {vuln.products.map((product) => (
                    <Badge key={product} variant="outline" className="capitalize">{product}</Badge>
                  ))}
                </div>
              </div>
            )}

            {vuln.affected_products && vuln.affected_products.length > 0 && (
              <details className="group">
                <summary className="text-sm font-semibold text-gray-900 dark:text-white cursor-pointer select-none">
                  Raw CPE Identifiers ({vuln.affected_products.length})
                </summary>
                <div className="space-y-1 max-h-64 overflow-y-auto mt-2">
                  {vuln.affected_products.map((product, idx) => (
                    <code
                      key={idx}
                      className="block bg-gray-50 dark:bg-gray-700 p-2 rounded text-xs font-mono text-gray-700 dark:text-gray-300"
                    >
                      {product}
                    </code>
                  ))}
                </div>
              </details>
            )}

            {vuln.sources && vuln.sources.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Data Sources
                </h3>
                <div className="flex flex-wrap gap-2">
                  {vuln.sources.map((source) => (
                    <Badge key={source} variant="secondary">{source}</Badge>
                  ))}
                </div>
              </div>
            )}
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
                      className="text-primary hover:underline break-all"
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

      {/* Comments Section */}
      <VulnerabilityComments cveId={cveId} />
    </div>
  );
}
