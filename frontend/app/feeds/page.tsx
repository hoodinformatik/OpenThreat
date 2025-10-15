"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Rss, AlertTriangle, TrendingUp, Copy, ExternalLink } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';

const feeds = [
  {
    title: "All Recent Vulnerabilities",
    description: "Latest vulnerabilities added to the database",
    url: `${API_URL}/api/v1/feeds/rss`,
    icon: Rss,
    color: "text-blue-600",
  },
  {
    title: "Exploited Vulnerabilities",
    description: "CVEs actively exploited in the wild (CISA KEV)",
    url: `${API_URL}/api/v1/feeds/exploited`,
    icon: AlertTriangle,
    color: "text-red-600",
  },
  {
    title: "Critical Vulnerabilities",
    description: "Only critical severity vulnerabilities",
    url: `${API_URL}/api/v1/feeds/critical`,
    icon: TrendingUp,
    color: "text-orange-600",
  },
];

export default function FeedsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">RSS Feeds</h1>
        <p className="text-gray-600 mt-1">
          Subscribe to vulnerability feeds in your favorite RSS reader
        </p>
      </div>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-3">
            <Rss className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-1">
                How to use RSS feeds
              </h3>
              <p className="text-sm text-blue-800">
                Copy the feed URL and add it to your RSS reader (e.g., Feedly, Inoreader, 
                NetNewsWire). You'll receive automatic updates when new vulnerabilities 
                matching your criteria are published.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Feeds List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {feeds.map((feed) => {
          const Icon = feed.icon;
          return (
            <Card key={feed.url} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-center space-x-2 mb-2">
                  <Icon className={`h-6 w-6 ${feed.color}`} />
                  <CardTitle className="text-lg">{feed.title}</CardTitle>
                </div>
                <CardDescription>{feed.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="bg-gray-50 p-3 rounded-md">
                  <code className="text-xs text-gray-700 break-all">
                    {feed.url}
                  </code>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onClick={() => {
                      navigator.clipboard.writeText(feed.url);
                    }}
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    Copy URL
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    asChild
                  >
                    <a
                      href={feed.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Popular RSS Readers */}
      <Card>
        <CardHeader>
          <CardTitle>Popular RSS Readers</CardTitle>
          <CardDescription>
            Choose an RSS reader to get started
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { name: "Feedly", url: "https://feedly.com" },
              { name: "Inoreader", url: "https://www.inoreader.com" },
              { name: "NewsBlur", url: "https://newsblur.com" },
              { name: "The Old Reader", url: "https://theoldreader.com" },
            ].map((reader) => (
              <a
                key={reader.name}
                href={reader.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <span className="font-medium text-gray-900">{reader.name}</span>
                <ExternalLink className="h-4 w-4 text-gray-400" />
              </a>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* API Documentation */}
      <Card>
        <CardHeader>
          <CardTitle>Feed Parameters</CardTitle>
          <CardDescription>
            Customize your feeds with URL parameters
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">
                Available Parameters:
              </h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex items-start">
                  <code className="bg-gray-100 px-2 py-1 rounded text-xs mr-2">
                    limit
                  </code>
                  <span>Number of items to return (default: 50, max: 100)</span>
                </li>
                <li className="flex items-start">
                  <code className="bg-gray-100 px-2 py-1 rounded text-xs mr-2">
                    exploited_only
                  </code>
                  <span>Only show exploited vulnerabilities (true/false)</span>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Example:</h4>
              <code className="block bg-gray-100 p-3 rounded text-xs">
                {API_URL}/api/v1/feeds/rss?limit=20&exploited_only=true
              </code>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
