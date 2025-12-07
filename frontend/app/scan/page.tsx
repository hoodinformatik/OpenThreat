"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  FileCode,
  AlertTriangle,
  Shield,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Package,
  Loader2,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

interface Vulnerability {
  cve_id: string;
  severity: string | null;
  cvss_score: number | null;
  title: string | null;
  description: string | null;
  match_type: string;
  match_confidence: number;
  exploited: boolean;
}

interface PackageWithVulns {
  name: string;
  version: string | null;
  ecosystem: string;
  dev: boolean;
  status: "safe" | "vulnerable";
  vulnerabilities: Vulnerability[];
}

interface ScanResult {
  id: number;
  name: string;
  source_type: string | null;
  package_count: number;
  vulnerable_count: number;
  safe_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  packages: PackageWithVulns[];
  session_id: string | null;
}

interface SupportedFormat {
  filename: string;
  ecosystem: string;
  language: string;
  description: string;
}

const severityColors: Record<string, string> = {
  CRITICAL: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  HIGH: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
  MEDIUM: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
  LOW: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  UNKNOWN: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
};

interface ScanProgress {
  phase: "parsing" | "scanning" | "fetching" | "complete";
  currentPackage: string;
  currentIndex: number;
  totalPackages: number;
  scannedPackages: string[];
  foundVulnerabilities: number;
}

export default function ScanPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [expandedPackages, setExpandedPackages] = useState<Set<string>>(new Set());
  const [formats, setFormats] = useState<SupportedFormat[]>([]);
  const [progress, setProgress] = useState<ScanProgress | null>(null);

  // Fetch supported formats on mount
  useState(() => {
    fetch(`${API_URL}/api/v1/techstack/formats`)
      .then((res) => res.json())
      .then((data) => setFormats(data.formats || []))
      .catch(console.error);
  });

  // Simulate progress animation for better UX
  const simulateProgress = useCallback(async (packages: string[], onComplete: () => void) => {
    setProgress({
      phase: "scanning",
      currentPackage: "",
      currentIndex: 0,
      totalPackages: packages.length,
      scannedPackages: [],
      foundVulnerabilities: 0,
    });

    // Animate through packages
    for (let i = 0; i < packages.length; i++) {
      setProgress((prev) => ({
        ...prev!,
        phase: "scanning",
        currentPackage: packages[i],
        currentIndex: i + 1,
        scannedPackages: [...(prev?.scannedPackages || []), packages[i]],
      }));
      // Faster for many packages, slower for few
      const delay = packages.length > 50 ? 30 : packages.length > 20 ? 50 : 100;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }

    setProgress((prev) => ({
      ...prev!,
      phase: "complete",
    }));

    onComplete();
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setIsLoading(true);
    setError(null);
    setResult(null);
    setProgress({ phase: "parsing", currentPackage: "", currentIndex: 0, totalPackages: 0, scannedPackages: [], foundVulnerabilities: 0 });

    try {
      // Parse the file client-side to avoid Cloudflare blocking file uploads
      const fileContent = await file.text();
      let packages: Array<{ name: string; version: string | null; ecosystem: string; dev: boolean }> = [];
      let ecosystem = "npm";

      // Parse based on file type (check extension and common names)
      const fileName = file.name.toLowerCase();
      const isPackageJson = fileName === "package.json" || fileName.endsWith("package.json");
      const isPackageLock = fileName === "package-lock.json" || fileName.endsWith("package-lock.json");
      const isRequirementsTxt = fileName === "requirements.txt" || fileName.endsWith(".txt") || fileName.includes("requirements");
      const isGemfile = fileName === "gemfile" || fileName === "gemfile.lock" || fileName.startsWith("gemfile");
      const isComposerJson = fileName === "composer.json" || fileName.endsWith("composer.json");
      const isGoMod = fileName === "go.mod" || fileName.endsWith(".mod");
      const isCargoToml = fileName === "cargo.toml" || fileName.endsWith("cargo.toml");
      const isPomXml = fileName === "pom.xml" || fileName.endsWith(".xml");

      if (isPackageJson || isPackageLock) {
        try {
          const json = JSON.parse(fileContent);
          ecosystem = "npm";

          // Parse dependencies
          if (json.dependencies) {
            for (const [name, version] of Object.entries(json.dependencies)) {
              packages.push({
                name,
                version: typeof version === "string" ? version.replace(/^[\^~>=<]/, "") : null,
                ecosystem: "npm",
                dev: false,
              });
            }
          }

          // Parse devDependencies
          if (json.devDependencies) {
            for (const [name, version] of Object.entries(json.devDependencies)) {
              packages.push({
                name,
                version: typeof version === "string" ? version.replace(/^[\^~>=<]/, "") : null,
                ecosystem: "npm",
                dev: true,
              });
            }
          }
        } catch {
          throw new Error("Invalid package.json format");
        }
      } else if (isRequirementsTxt) {
        ecosystem = "pypi";
        const lines = fileContent.split("\n");

        for (const line of lines) {
          const trimmed = line.trim();
          // Skip comments, empty lines, and flags
          if (!trimmed || trimmed.startsWith("#") || trimmed.startsWith("-")) continue;

          // Parse package==version, package>=version, etc.
          const match = trimmed.match(/^([a-zA-Z0-9_-]+)(?:\[.*?\])?(?:([=<>!~]+)(.+))?$/);
          if (match) {
            packages.push({
              name: match[1],
              version: match[3] || null,
              ecosystem: "pypi",
              dev: false,
            });
          }
        }
      } else if (isGemfile) {
        ecosystem = "rubygems";
        // Simple Gemfile parsing
        const gemRegex = /gem\s+['"]([^'"]+)['"](?:,\s*['"]([^'"]+)['"])?/g;
        let match;
        while ((match = gemRegex.exec(fileContent)) !== null) {
          packages.push({
            name: match[1],
            version: match[2] || null,
            ecosystem: "rubygems",
            dev: false,
          });
        }
      } else if (isComposerJson) {
        ecosystem = "packagist";
        try {
          const json = JSON.parse(fileContent);
          const allDeps = { ...json.require, ...json["require-dev"] };
          for (const [name, version] of Object.entries(allDeps)) {
            if (name === "php") continue; // Skip PHP version requirement
            packages.push({
              name,
              version: typeof version === "string" ? version : null,
              ecosystem: "packagist",
              dev: false,
            });
          }
        } catch {
          throw new Error("Invalid composer.json format");
        }
      } else if (isGoMod) {
        ecosystem = "go";
        const requireRegex = /require\s+([^\s]+)\s+v?([^\s]+)/g;
        let match;
        while ((match = requireRegex.exec(fileContent)) !== null) {
          packages.push({
            name: match[1],
            version: match[2],
            ecosystem: "go",
            dev: false,
          });
        }
      } else if (isCargoToml) {
        ecosystem = "cargo";
        // Simple Cargo.toml parsing
        const depRegex = /^([a-zA-Z0-9_-]+)\s*=\s*["']([^"']+)["']/gm;
        let match;
        while ((match = depRegex.exec(fileContent)) !== null) {
          packages.push({
            name: match[1],
            version: match[2],
            ecosystem: "cargo",
            dev: false,
          });
        }
      } else if (isPomXml) {
        ecosystem = "maven";
        // Simple pom.xml parsing
        const depRegex = /<artifactId>([^<]+)<\/artifactId>[\s\S]*?<version>([^<]+)<\/version>/g;
        let match;
        while ((match = depRegex.exec(fileContent)) !== null) {
          packages.push({
            name: match[1],
            version: match[2],
            ecosystem: "maven",
            dev: false,
          });
        }
      } else {
        throw new Error(`Unsupported file format: ${file.name}`);
      }

      if (packages.length === 0) {
        throw new Error("No packages found in the file. Please check the file format.");
      }

      const packageNames = packages.map((p) => p.name);

      // Use POST endpoint with JSON body for robust data transfer
      // Encode payload as base64 to avoid Cloudflare blocking special characters in package names
      const payload = {
        name: `Scan of ${file.name}`,
        packages: packages,
      };
      const jsonPayload = JSON.stringify(payload);
      const encodedPayload = btoa(unescape(encodeURIComponent(jsonPayload)));

      const apiPromise = fetch(`${API_URL}/api/v1/techstack/scan/manual/encoded`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ encoded: encodedPayload }),
      });

      // Run progress animation and API request in parallel
      let apiResponse: Response | null = null;
      let apiError: Error | null = null;

      // Start API request
      const apiPromiseWithCapture = apiPromise
        .then((res) => { apiResponse = res; })
        .catch((err) => { apiError = err; });

      // Run progress animation
      await simulateProgress(packageNames, () => {});

      // Show fetching state if API hasn't responded yet
      if (!apiResponse && !apiError) {
        setProgress((prev) => ({
          ...prev!,
          phase: "fetching",
        }));
        await apiPromiseWithCapture;
      }

      if (apiError) {
        throw apiError;
      }

      const response = apiResponse!;

      // Read response body once
      const responseText = await response.text();

      if (!response.ok) {
        let errorMessage = "Failed to scan file";
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || errorMessage;
        } catch {
          // Response might not be JSON (e.g., Cloudflare HTML page)
          if (responseText.includes("Just a moment") || responseText.includes("cloudflare")) {
            errorMessage = "Request blocked by security. Please try again in a few seconds.";
          }
        }
        throw new Error(errorMessage);
      }

      let data;
      try {
        data = JSON.parse(responseText);
      } catch {
        throw new Error("Invalid response from server. Please try again.");
      }

      // Update progress with final vulnerability count
      setProgress((prev) => ({
        ...prev!,
        foundVulnerabilities: data.vulnerable_count,
      }));

      // Small delay to show completion
      await new Promise((resolve) => setTimeout(resolve, 500));

      setResult(data);
      setProgress(null);

      // Auto-expand packages with vulnerabilities
      const vulnPackages = new Set<string>(
        data.packages
          .filter((p: PackageWithVulns) => p.vulnerabilities.length > 0)
          .map((p: PackageWithVulns) => p.name)
      );
      setExpandedPackages(vulnPackages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setProgress(null);
    } finally {
      setIsLoading(false);
    }
  }, [simulateProgress]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/json": [".json"],
      "text/plain": [".txt", ".toml", ".lock", ".mod"],
      "application/xml": [".xml"],
    },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024, // 5MB
  });

  const togglePackage = (packageName: string) => {
    setExpandedPackages((prev) => {
      const next = new Set(prev);
      if (next.has(packageName)) {
        next.delete(packageName);
      } else {
        next.add(packageName);
      }
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pt-20 pb-12">
      <div className="container mx-auto px-4 max-w-5xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Tech Stack Vulnerability Scanner
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Upload your dependency file to check for known CVE vulnerabilities
          </p>
        </div>

        {/* Upload Area */}
        {!result && !progress && (
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
              transition-all duration-200
              ${
                isDragActive
                  ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                  : "border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500"
              }
            `}
          >
            <input {...getInputProps()} />
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-lg text-gray-700 dark:text-gray-300 mb-2">
              {isDragActive
                ? "Drop your file here..."
                : "Drag & drop your dependency file here"}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              or click to browse
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {["package.json", "requirements.txt", "Gemfile", "pom.xml", "go.mod"].map(
                (file) => (
                  <span
                    key={file}
                    className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm text-gray-600 dark:text-gray-300"
                  >
                    {file}
                  </span>
                )
              )}
            </div>
          </div>
        )}

        {/* Progress Display */}
        {progress && !result && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Progress Header */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  {progress.phase === "parsing" ? "Parsing file..." :
                   progress.phase === "fetching" ? (
                     <>
                       <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                       Analyzing vulnerabilities...
                     </>
                   ) :
                   progress.phase === "complete" ? "Scan complete!" : "Scanning for vulnerabilities..."}
                </h2>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {progress.currentIndex} / {progress.totalPackages} packages
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress.totalPackages > 0 ? (progress.currentIndex / progress.totalPackages) * 100 : 0}%` }}
                />
              </div>
            </div>

            {/* Current Package */}
            <div className="p-6 bg-gray-50 dark:bg-gray-900/50">
              <div className="flex items-center space-x-3 mb-4">
                <div className="relative">
                  <Package className="h-6 w-6 text-blue-500" />
                  {(progress.phase === "scanning" || progress.phase === "fetching") && (
                    <span className="absolute -top-1 -right-1 h-3 w-3 bg-blue-500 rounded-full animate-ping" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {progress.phase === "fetching" ? "Matching against CVE database:" : "Currently checking:"}
                  </p>
                  <p className="text-lg font-mono font-medium text-gray-900 dark:text-white truncate">
                    {progress.phase === "fetching"
                      ? `${progress.totalPackages} packages`
                      : (progress.currentPackage || "Initializing...")}
                  </p>
                </div>
                {(progress.phase === "scanning" || progress.phase === "fetching") && (
                  <Loader2 className="h-5 w-5 text-blue-500 animate-spin flex-shrink-0" />
                )}
                {progress.phase === "complete" && (
                  <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                )}
              </div>

              {/* Scanned Packages List (last 5) */}
              <div className="space-y-1">
                <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
                  Recently scanned:
                </p>
                <div className="flex flex-wrap gap-2">
                  {progress.scannedPackages.slice(-8).map((pkg, idx) => (
                    <span
                      key={`${pkg}-${idx}`}
                      className={`
                        px-2 py-1 text-xs rounded-md font-mono
                        ${idx === progress.scannedPackages.slice(-8).length - 1
                          ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
                          : "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
                        }
                      `}
                    >
                      {pkg}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Stats Preview */}
            {progress.phase === "complete" && progress.foundVulnerabilities > 0 && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border-t border-red-200 dark:border-red-800">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-5 w-5 text-red-500" />
                  <span className="text-red-700 dark:text-red-300 font-medium">
                    Found {progress.foundVulnerabilities} vulnerable package{progress.foundVulnerabilities !== 1 ? "s" : ""}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center">
              <XCircle className="h-5 w-5 text-red-500 mr-2" />
              <p className="text-red-700 dark:text-red-300">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <Package className="h-6 w-6 text-blue-500" />
                  <span className="text-2xl font-bold text-gray-900 dark:text-white">
                    {result.package_count}
                  </span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Total
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-green-200 dark:border-green-800">
                <div className="flex items-center justify-between">
                  <CheckCircle className="h-6 w-6 text-green-500" />
                  <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {result.safe_count}
                  </span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Safe
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-orange-200 dark:border-orange-800">
                <div className="flex items-center justify-between">
                  <AlertTriangle className="h-6 w-6 text-orange-500" />
                  <span className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    {result.vulnerable_count}
                  </span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Vulnerable
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-red-200 dark:border-red-800">
                <div className="flex items-center justify-between">
                  <XCircle className="h-6 w-6 text-red-500" />
                  <span className="text-2xl font-bold text-red-600 dark:text-red-400">
                    {result.critical_count}
                  </span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Critical
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-orange-200 dark:border-orange-800">
                <div className="flex items-center justify-between">
                  <Shield className="h-6 w-6 text-orange-500" />
                  <span className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    {result.high_count}
                  </span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  High
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-yellow-200 dark:border-yellow-800">
                <div className="flex items-center justify-between">
                  <AlertTriangle className="h-6 w-6 text-yellow-500" />
                  <span className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                    {result.medium_count + result.low_count}
                  </span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Medium/Low
                </p>
              </div>
            </div>

            {/* All Clear Message */}
            {result.vulnerable_count === 0 && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-8 text-center">
                <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-green-700 dark:text-green-300 mb-2">
                  All Clear! 🎉
                </h2>
                <p className="text-green-600 dark:text-green-400">
                  No known vulnerabilities found in your {result.package_count} packages.
                </p>
              </div>
            )}

            {/* Vulnerabilities Found Warning */}
            {result.vulnerable_count > 0 && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="h-8 w-8 text-red-500 flex-shrink-0" />
                  <div>
                    <h2 className="text-xl font-bold text-red-700 dark:text-red-300">
                      Vulnerabilities Detected!
                    </h2>
                    <p className="text-red-600 dark:text-red-400">
                      Found {result.vulnerable_count} vulnerable package{result.vulnerable_count !== 1 ? "s" : ""} with{" "}
                      {result.critical_count > 0 && <span className="font-bold">{result.critical_count} critical</span>}
                      {result.critical_count > 0 && result.high_count > 0 && " and "}
                      {result.high_count > 0 && <span className="font-bold">{result.high_count} high</span>}
                      {" "}severity issues.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Scan Again Button */}
            <div className="flex justify-center">
              <button
                onClick={() => {
                  setResult(null);
                  setError(null);
                }}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
              >
                Scan Another File
              </button>
            </div>

            {/* All Packages List */}
            {result.packages.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    All Dependencies ({result.package_count})
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {result.vulnerable_count > 0 ? (
                      <>
                        <span className="text-red-600 dark:text-red-400 font-medium">{result.vulnerable_count} vulnerable</span>
                        {" • "}
                        <span className="text-green-600 dark:text-green-400 font-medium">{result.safe_count} safe</span>
                      </>
                    ) : (
                      <span className="text-green-600 dark:text-green-400 font-medium">All packages are safe</span>
                    )}
                  </p>
                </div>

                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {result.packages.map((pkg) => (
                    <div
                      key={pkg.name}
                      className={`p-4 ${
                        pkg.status === "vulnerable"
                          ? "bg-red-50/50 dark:bg-red-900/10"
                          : ""
                      }`}
                    >
                      <div
                        className={`flex items-center justify-between ${
                          pkg.status === "vulnerable" ? "cursor-pointer" : ""
                        }`}
                        onClick={() => pkg.status === "vulnerable" && togglePackage(pkg.name)}
                      >
                        <div className="flex items-center space-x-3">
                          {pkg.status === "vulnerable" ? (
                            <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0" />
                          ) : (
                            <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                          )}
                          <div className="min-w-0">
                            <span className="font-medium text-gray-900 dark:text-white">
                              {pkg.name}
                            </span>
                            {pkg.version && (
                              <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                                v{pkg.version}
                              </span>
                            )}
                            {pkg.dev && (
                              <span className="ml-2 px-1.5 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                                dev
                              </span>
                            )}
                          </div>
                          <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                            {pkg.ecosystem}
                          </span>
                        </div>

                        <div className="flex items-center space-x-3">
                          {pkg.status === "vulnerable" ? (
                            <>
                              <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
                                {pkg.vulnerabilities.length} CVE{pkg.vulnerabilities.length !== 1 ? "s" : ""}
                              </span>
                              {expandedPackages.has(pkg.name) ? (
                                <ChevronUp className="h-5 w-5 text-gray-400" />
                              ) : (
                                <ChevronDown className="h-5 w-5 text-gray-400" />
                              )}
                            </>
                          ) : (
                            <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                              No CVEs
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Expanded Vulnerabilities */}
                      {pkg.status === "vulnerable" && expandedPackages.has(pkg.name) && (
                        <div className="mt-4 space-y-3 pl-8">
                          {pkg.vulnerabilities.map((vuln) => (
                            <div
                              key={vuln.cve_id}
                              className="p-3 bg-white dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600"
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                                  <a
                                    href={`/vulnerabilities?search=${vuln.cve_id}`}
                                    className="font-mono text-blue-600 dark:text-blue-400 hover:underline"
                                  >
                                    {vuln.cve_id}
                                  </a>
                                  <span
                                    className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                                      severityColors[vuln.severity || "UNKNOWN"]
                                    }`}
                                  >
                                    {vuln.severity || "UNKNOWN"}
                                  </span>
                                  {vuln.exploited && (
                                    <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
                                      Exploited in Wild
                                    </span>
                                  )}
                                </div>
                                {vuln.cvss_score && (
                                  <span className="text-sm font-medium text-gray-600 dark:text-gray-300 flex-shrink-0">
                                    CVSS: {vuln.cvss_score.toFixed(1)}
                                  </span>
                                )}
                              </div>
                              {vuln.title && (
                                <p className="mt-2 text-sm font-medium text-gray-800 dark:text-gray-200">
                                  {vuln.title}
                                </p>
                              )}
                              {vuln.description && (
                                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                                  {vuln.description}
                                </p>
                              )}
                              <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                                <span>
                                  Match: {vuln.match_type.replace(/_/g, " ")}
                                </span>
                                <span>
                                  Confidence: {(vuln.match_confidence * 100).toFixed(0)}%
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Supported Formats */}
        {!result && formats.length > 0 && (
          <div className="mt-12">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 text-center">
              Supported File Formats
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {formats.map((format) => (
                <div
                  key={format.filename}
                  className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-center space-x-3">
                    <FileCode className="h-8 w-8 text-blue-500" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {format.filename}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {format.language} • {format.ecosystem}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
