"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Flag, ExternalLink, Shield } from "lucide-react";

interface BSIAdvisory {
  advisory_id: string;
  title: string;
  description: string;
  link: string;
  published_at: string | null;
  cve_ids: string[];
  severity: string | null;
  source: string;
}

export default function BSIAdvisoriesPage() {
  const [advisories, setAdvisories] = useState<BSIAdvisory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAdvisories();
  }, []);

  const fetchAdvisories = async () => {
    try {
      setLoading(true);
      // This would call a new API endpoint that returns BSI advisories
      // For now, we'll show a placeholder
      setError("API endpoint not yet implemented");
    } catch (err) {
      setError("Failed to fetch BSI advisories");
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string | null) => {
    if (!severity) return "bg-gray-100 text-gray-800";
    
    switch (severity.toUpperCase()) {
      case "CRITICAL":
        return "bg-red-100 text-red-800 border-red-300";
      case "HIGH":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "MEDIUM":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "LOW":
        return "bg-green-100 text-green-800 border-green-300";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-3 mb-2">
          <Flag className="h-8 w-8 text-amber-600" />
          <h1 className="text-3xl font-bold text-gray-900">
            🇩🇪 BSI CERT-Bund Advisories
          </h1>
        </div>
        <p className="text-gray-600">
          Security advisories from the German Federal Office for Information Security (BSI)
        </p>
      </div>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-3">
            <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-1">
                About BSI CERT-Bund
              </h3>
              <p className="text-sm text-blue-800">
                The German Computer Emergency Response Team (CERT-Bund) provides security advisories
                for vulnerabilities affecting German organizations and citizens. These advisories
                include German-language descriptions, severity ratings, and official recommendations.
              </p>
              <a
                href="https://wid.cert-bund.de/portal/wid/securityadvisory"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700 mt-2"
              >
                Visit BSI CERT-Bund Portal
                <ExternalLink className="h-3 w-3 ml-1" />
              </a>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Coming Soon */}
      <Card>
        <CardHeader>
          <CardTitle>BSI Advisory Integration</CardTitle>
          <CardDescription>
            This feature is currently in development
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Shield className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Coming Soon
            </h3>
            <p className="text-gray-600 mb-4">
              We're working on integrating BSI CERT-Bund advisories directly into OpenThreat.
              This will include:
            </p>
            <ul className="text-left max-w-md mx-auto space-y-2 text-gray-600">
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">✓</span>
                German-language vulnerability descriptions
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">✓</span>
                BSI severity ratings and recommendations
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">✓</span>
                Direct links to official BSI advisories
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">✓</span>
                Automatic enrichment of CVE data
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Manual Check */}
      <Card>
        <CardHeader>
          <CardTitle>Check BSI CERT-Bund Manually</CardTitle>
          <CardDescription>
            Visit the official BSI portal for the latest security advisories
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <a
              href="https://wid.cert-bund.de/portal/wid/securityadvisory"
              target="_blank"
              rel="noopener noreferrer"
              className="block"
            >
              <Button variant="outline" className="w-full justify-between">
                <span>BSI Security Advisories Portal</span>
                <ExternalLink className="h-4 w-4" />
              </Button>
            </a>
            <a
              href="https://wid.cert-bund.de/content/public/securityAdvisory/rss"
              target="_blank"
              rel="noopener noreferrer"
              className="block"
            >
              <Button variant="outline" className="w-full justify-between">
                <span>BSI RSS Feed</span>
                <ExternalLink className="h-4 w-4" />
              </Button>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
