import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, Heart, Users, Book, Github, Mail } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="text-center space-y-4">
        <Shield className="h-16 w-16 text-blue-600 mx-auto" />
        <h1 className="text-4xl font-bold text-gray-900">About OpenThreat</h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Democratizing threat intelligence for everyone - from security professionals
          to small businesses and non-profits.
        </p>
      </div>

      {/* Mission */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Heart className="h-6 w-6 text-red-600" />
            <span>Our Mission</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-700 leading-relaxed">
            Security information shouldn't be locked behind expensive subscriptions or
            complex technical jargon. OpenThreat makes threat intelligence accessible
            to everyone by:
          </p>
          <ul className="space-y-2 text-gray-700">
            <li className="flex items-start">
              <span className="font-semibold mr-2">•</span>
              <span>
                <strong>Aggregating public data sources</strong> - We collect vulnerability
                information from CISA, NVD, and other trusted public sources
              </span>
            </li>
            <li className="flex items-start">
              <span className="font-semibold mr-2">•</span>
              <span>
                <strong>Explaining in plain language</strong> - No security degree required.
                We translate technical details into actionable advice
              </span>
            </li>
            <li className="flex items-start">
              <span className="font-semibold mr-2">•</span>
              <span>
                <strong>Prioritizing what matters</strong> - Our scoring system helps you
                focus on the most critical threats first
              </span>
            </li>
            <li className="flex items-start">
              <span className="font-semibold mr-2">•</span>
              <span>
                <strong>Staying free and open-source</strong> - Security is a right, not
                a privilege. Our code and data are always free
              </span>
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* For Who */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Security Professionals</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>• Comprehensive CVE database</li>
              <li>• Priority scoring for triage</li>
              <li>• REST API for integration</li>
              <li>• RSS feeds for monitoring</li>
              <li>• Advanced search & filtering</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Small Businesses & NGOs</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>• Free and easy to use</li>
              <li>• Plain-language explanations</li>
              <li>• Clear action recommendations</li>
              <li>• No security expertise needed</li>
              <li>• Self-hosted option available</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Developers</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>• Open-source codebase</li>
              <li>• Well-documented API</li>
              <li>• Extensible architecture</li>
              <li>• Multiple data connectors</li>
              <li>• Docker deployment</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Data Sources */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Book className="h-6 w-6 text-blue-600" />
            <span>Data Sources</span>
          </CardTitle>
          <CardDescription>
            We aggregate data from trusted public sources
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">
                CISA Known Exploited Vulnerabilities (KEV)
              </h4>
              <p className="text-sm text-gray-700">
                The U.S. Cybersecurity and Infrastructure Security Agency maintains
                a catalog of vulnerabilities actively exploited in the wild.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">
                National Vulnerability Database (NVD)
              </h4>
              <p className="text-sm text-gray-700">
                NIST's comprehensive database of CVEs with CVSS scores, CWE
                classifications, and affected products.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">
                CVE Search (CIRCL)
              </h4>
              <p className="text-sm text-gray-700">
                European CVE search engine providing additional vulnerability
                metadata and cross-references.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">
                MITRE ATT&CK Framework
              </h4>
              <p className="text-sm text-gray-700">
                Knowledge base of adversary tactics and techniques based on
                real-world observations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* How It Works */}
      <Card>
        <CardHeader>
          <CardTitle>How It Works</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                1
              </div>
              <div>
                <h4 className="font-semibold text-gray-900">Data Collection</h4>
                <p className="text-sm text-gray-700">
                  We automatically collect vulnerability data from multiple public
                  sources every few hours.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                2
              </div>
              <div>
                <h4 className="font-semibold text-gray-900">Deduplication & Enrichment</h4>
                <p className="text-sm text-gray-700">
                  We merge data from different sources, remove duplicates, and enrich
                  with additional context.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                3
              </div>
              <div>
                <h4 className="font-semibold text-gray-900">Priority Scoring</h4>
                <p className="text-sm text-gray-700">
                  Our algorithm calculates priority scores based on exploitation status
                  (50%), CVSS score (40%), and recency (10%).
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                4
              </div>
              <div>
                <h4 className="font-semibold text-gray-900">Plain-Language Translation</h4>
                <p className="text-sm text-gray-700">
                  We generate easy-to-understand explanations and action recommendations
                  for each vulnerability.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                5
              </div>
              <div>
                <h4 className="font-semibold text-gray-900">Accessible Interface</h4>
                <p className="text-sm text-gray-700">
                  Everything is presented through our web interface, API, and RSS feeds
                  - choose what works best for you.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tech Stack */}
      <Card>
        <CardHeader>
          <CardTitle>Technology</CardTitle>
          <CardDescription>Built with modern, reliable tools</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Frontend</h4>
              <ul className="text-gray-700 space-y-1">
                <li>Next.js 14</li>
                <li>React 18</li>
                <li>TypeScript</li>
                <li>TailwindCSS</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Backend</h4>
              <ul className="text-gray-700 space-y-1">
                <li>Python 3.13</li>
                <li>FastAPI</li>
                <li>SQLAlchemy</li>
                <li>Pydantic</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Database</h4>
              <ul className="text-gray-700 space-y-1">
                <li>PostgreSQL 16</li>
                <li>Redis 7</li>
                <li>Alembic</li>
                <li>Full-text search</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Deployment</h4>
              <ul className="text-gray-700 space-y-1">
                <li>Docker</li>
                <li>Docker Compose</li>
                <li>Uvicorn</li>
                <li>Self-hosted</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Get Involved */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="h-6 w-6 text-blue-600" />
            <span>Get Involved</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-700">
            OpenThreat is open-source and community-driven. We welcome contributions!
          </p>
          <div className="flex flex-wrap gap-4">
            <a
              href="https://github.com/yourusername/openthreat"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 transition-colors"
            >
              <Github className="h-5 w-5" />
              <span>View on GitHub</span>
            </a>
            <a
              href="mailto:contact@openthreat.io"
              className="inline-flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              <Mail className="h-5 w-5" />
              <span>Contact Us</span>
            </a>
          </div>
        </CardContent>
      </Card>

      {/* License */}
      <Card>
        <CardHeader>
          <CardTitle>License & Legal</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Open Source License</h4>
            <p className="text-sm text-gray-700">
              OpenThreat is licensed under the Apache License 2.0. You're free to use,
              modify, and distribute this software, even for commercial purposes.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Data Sources</h4>
            <p className="text-sm text-gray-700">
              All vulnerability data comes from public sources. We do not store or
              distribute any proprietary or confidential information.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Disclaimer</h4>
            <p className="text-sm text-gray-700">
              While we strive for accuracy, this information is provided "as is" without
              warranty. Always verify critical security information with official sources.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
