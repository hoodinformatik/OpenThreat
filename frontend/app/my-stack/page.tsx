"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useDropzone } from "react-dropzone";
import Link from "next/link";
import {
  Upload,
  Plus,
  Trash2,
  Download,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Sparkles,
  FileJson,
  Shield,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getSeverityBadgeColor } from "@/lib/utils";
import { parseDependencyFile } from "@/lib/techstack-parsers";
import {
  Stack,
  loadStacks,
  saveStacks,
  createStack,
  exportStacksToFile,
  importStacksFromFile,
} from "@/lib/stacks-storage";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

interface MatchedVuln {
  cve_id: string;
  severity: string | null;
  cvss_score: number | null;
  title: string | null;
  exploited: boolean;
  published_at: string | null;
}

interface MatchResult {
  package_count: number;
  vulnerable_count: number;
  critical_count: number;
  high_count: number;
  packages: Array<{
    name: string;
    version: string | null;
    status: "safe" | "vulnerable";
    vulnerabilities: MatchedVuln[];
  }>;
}

export default function MyStackPage() {
  const [stacks, setStacks] = useState<Stack[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, MatchResult>>({});
  const [checking, setChecking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const importInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const loaded = loadStacks();
    setStacks(loaded);
    if (loaded.length > 0) setActiveId(loaded[0].id);
  }, []);

  const activeStack = stacks.find((s) => s.id === activeId) || null;

  const checkStack = useCallback(async (stack: Stack) => {
    setChecking(stack.id);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/techstack/match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ packages: stack.packages }),
      });
      if (!res.ok) throw new Error("Failed to check stack against current CVEs");
      const data: MatchResult = await res.json();
      setResults((prev) => ({ ...prev, [stack.id]: data }));

      setStacks((prev) => {
        const updated = prev.map((s) =>
          s.id === stack.id ? { ...s, lastCheckedAt: new Date().toISOString() } : s
        );
        saveStacks(updated);
        return updated;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to check stack");
    } finally {
      setChecking(null);
    }
  }, []);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      const file = acceptedFiles[0];
      setError(null);

      try {
        const content = await file.text();
        const packages = parseDependencyFile(file.name, content);
        const stack = createStack(file.name.replace(/\.[^.]+$/, "") || "My Stack", packages);

        const updated = [...stacks, stack];
        setStacks(updated);
        saveStacks(updated);
        setActiveId(stack.id);
        checkStack(stack);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to parse file");
      }
    },
    [stacks, checkStack]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/json": [".json"],
      "text/plain": [".txt", ".toml", ".lock", ".mod"],
      "application/xml": [".xml"],
    },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024,
  });

  const deleteStack = (id: string) => {
    const updated = stacks.filter((s) => s.id !== id);
    setStacks(updated);
    saveStacks(updated);
    setResults((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
    if (activeId === id) setActiveId(updated[0]?.id ?? null);
  };

  const handleExport = () => exportStacksToFile(stacks);

  const handleImportClick = () => importInputRef.current?.click();

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    try {
      const imported = await importStacksFromFile(file);
      const merged = [...stacks, ...imported];
      setStacks(merged);
      saveStacks(merged);
      if (imported.length > 0) setActiveId(imported[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to import file");
    }
  };

  const isNew = (stack: Stack, publishedAt: string | null) => {
    if (!stack.lastCheckedAt || !publishedAt) return false;
    return new Date(publishedAt) > new Date(stack.lastCheckedAt);
  };

  const activeResult = activeStack ? results[activeStack.id] : null;

  return (
    <div className="space-y-8">
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold tracking-wide uppercase">
          <Shield className="h-3.5 w-3.5" />
          Privacy-First
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">
          My Tech Stack
        </h1>
        <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          Track the software you use and see which CVEs affect it. Your stack is saved only in
          this browser (never on our servers) - export it to back it up or move it to another device.
        </p>
      </div>

      {error && (
        <div className="max-w-2xl mx-auto p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar: stack list */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Your Stacks</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {stacks.length === 0 && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No stacks yet. Add one below.
                </p>
              )}
              {stacks.map((stack) => {
                const result = results[stack.id];
                return (
                  <button
                    key={stack.id}
                    onClick={() => setActiveId(stack.id)}
                    className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                      activeId === stack.id
                        ? "bg-primary/10 text-primary font-medium"
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate">{stack.name}</span>
                      {result && result.vulnerable_count > 0 && (
                        <Badge className="bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400 border-red-300 dark:border-red-700 flex-shrink-0">
                          {result.vulnerable_count}
                        </Badge>
                      )}
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {stack.packages.length} packages
                    </span>
                  </button>
                );
              })}
            </CardContent>
          </Card>

          {/* Add stack dropzone */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors text-sm ${
              isDragActive
                ? "border-primary bg-primary/5"
                : "border-gray-300 dark:border-gray-600 hover:border-primary"
            }`}
          >
            <input {...getInputProps()} />
            <Plus className="h-5 w-5 mx-auto mb-1 text-gray-400" />
            <p className="text-gray-600 dark:text-gray-400">
              {isDragActive ? "Drop file here" : "Drop a dependency file to add a stack"}
            </p>
          </div>

          {/* Export / Import */}
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="flex-1" onClick={handleExport} disabled={stacks.length === 0}>
              <Download className="h-4 w-4 mr-1" />
              Export
            </Button>
            <Button variant="outline" size="sm" className="flex-1" onClick={handleImportClick}>
              <FileJson className="h-4 w-4 mr-1" />
              Import
            </Button>
            <input
              ref={importInputRef}
              type="file"
              accept="application/json"
              className="hidden"
              onChange={handleImportFile}
            />
          </div>
        </div>

        {/* Main: active stack results */}
        <div className="lg:col-span-3 space-y-4">
          {!activeStack ? (
            <Card>
              <CardContent className="py-12 text-center text-gray-500 dark:text-gray-400">
                Add a stack to see which CVEs affect it.
              </CardContent>
            </Card>
          ) : (
            <>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>{activeStack.name}</CardTitle>
                      <CardDescription>
                        {activeStack.packages.length} packages
                        {activeStack.lastCheckedAt && (
                          <> · last checked {new Date(activeStack.lastCheckedAt).toLocaleString()}</>
                        )}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => checkStack(activeStack)}
                        disabled={checking === activeStack.id}
                      >
                        <RefreshCw className={`h-4 w-4 mr-1 ${checking === activeStack.id ? "animate-spin" : ""}`} />
                        {checking === activeStack.id ? "Checking..." : "Check Now"}
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => deleteStack(activeStack.id)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
              </Card>

              {activeResult && (
                <>
                  {activeResult.vulnerable_count === 0 ? (
                    <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-8 text-center">
                      <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-3" />
                      <h2 className="text-xl font-bold text-green-700 dark:text-green-300">All Clear</h2>
                      <p className="text-green-600 dark:text-green-400 text-sm mt-1">
                        No known vulnerabilities found in {activeResult.package_count} packages.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {activeResult.packages
                        .filter((p) => p.status === "vulnerable")
                        .map((pkg) => (
                          <Card key={pkg.name}>
                            <CardContent className="pt-6">
                              <div className="flex items-center gap-2 mb-3">
                                <AlertTriangle className="h-4 w-4 text-red-500" />
                                <span className="font-semibold text-gray-900 dark:text-white">{pkg.name}</span>
                                {pkg.version && (
                                  <span className="text-sm text-gray-500 dark:text-gray-400">v{pkg.version}</span>
                                )}
                              </div>
                              <div className="space-y-2">
                                {pkg.vulnerabilities.map((vuln) => (
                                  <Link
                                    key={vuln.cve_id}
                                    href={`/vulnerabilities/${vuln.cve_id}`}
                                    className="block p-3 rounded-md border border-gray-200 dark:border-gray-700 hover:border-primary transition-colors"
                                  >
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <span className="font-mono text-sm font-semibold text-primary">
                                        {vuln.cve_id}
                                      </span>
                                      {vuln.severity && (
                                        <Badge className={getSeverityBadgeColor(vuln.severity)}>
                                          {vuln.severity}
                                        </Badge>
                                      )}
                                      {isNew(activeStack, vuln.published_at) && (
                                        <Badge className="bg-primary/10 text-primary border-primary/30">
                                          <Sparkles className="h-3 w-3 mr-1" />
                                          New
                                        </Badge>
                                      )}
                                    </div>
                                    {vuln.title && (
                                      <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{vuln.title}</p>
                                    )}
                                  </Link>
                                ))}
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
