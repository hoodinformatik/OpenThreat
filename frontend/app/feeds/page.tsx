"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Rss, AlertTriangle, TrendingUp, Copy, ExternalLink, Construction, Clock } from "lucide-react";

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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">RSS Feeds</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Subscribe to vulnerability feeds in your favorite RSS reader
        </p>
      </div>

      {/* Under Construction Banner */}
      <Card className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 border-amber-200 dark:border-amber-800">
        <CardContent className="pt-6 pb-6">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <div className="h-12 w-12 rounded-full bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center">
                <Construction className="h-6 w-6 text-amber-600 dark:text-amber-400" />
              </div>
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <h3 className="font-semibold text-amber-900 dark:text-amber-200 text-lg">
                  Feature Under Development
                </h3>
                <Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              </div>
              <p className="text-sm text-amber-800 dark:text-amber-300 mb-3">
                RSS feeds are currently being developed and will be available soon. We're working on providing 
                real-time vulnerability updates directly to your RSS reader.
              </p>
              <div className="flex items-center space-x-2 text-xs text-amber-700 dark:text-amber-400">
                <div className="flex items-center space-x-1">
                  <div className="h-2 w-2 rounded-full bg-amber-500 dark:bg-amber-400 animate-pulse"></div>
                  <span className="font-medium">Expected availability: Coming soon</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
