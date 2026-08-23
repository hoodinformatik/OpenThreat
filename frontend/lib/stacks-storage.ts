/**
 * Client-side storage for the tech-stack tracker. Stacks live entirely in
 * the browser's localStorage - nothing is ever sent to or stored on the
 * server except a one-shot package list for CVE matching (see
 * POST /api/v1/techstack/match, which persists nothing).
 */

import { ParsedPackage } from "./techstack-parsers";

export interface Stack {
  id: string;
  name: string;
  packages: ParsedPackage[];
  createdAt: string;
  lastCheckedAt: string | null;
}

const STORAGE_KEY = "openthreat_stacks";

export function loadStacks(): Stack[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveStacks(stacks: Stack[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stacks));
  } catch {
    // Storage unavailable (private browsing, quota, disabled) - fail silently,
    // the UI still works for the current session, it just won't persist.
  }
}

export function createStack(name: string, packages: ParsedPackage[]): Stack {
  return {
    id: crypto.randomUUID(),
    name,
    packages,
    createdAt: new Date().toISOString(),
    lastCheckedAt: null,
  };
}

export function exportStacksToFile(stacks: Stack[]): void {
  const blob = new Blob([JSON.stringify({ stacks }, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `openthreat-stacks-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function importStacksFromFile(file: File): Promise<Stack[]> {
  const text = await file.text();
  let data: any;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error("Invalid file: not valid JSON");
  }

  const stacks = Array.isArray(data) ? data : data.stacks;
  if (!Array.isArray(stacks)) {
    throw new Error("Invalid file: expected a stacks export from this site");
  }

  for (const stack of stacks) {
    if (typeof stack?.name !== "string" || !Array.isArray(stack?.packages)) {
      throw new Error("Invalid file: malformed stack entry");
    }
  }

  return stacks as Stack[];
}
