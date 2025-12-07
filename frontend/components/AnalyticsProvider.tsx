"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { trackPageView } from "@/lib/analytics";

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const lastPathRef = useRef<string | null>(null);

  useEffect(() => {
    // Only track if path changed (avoid double tracking on initial load)
    if (pathname && pathname !== lastPathRef.current) {
      lastPathRef.current = pathname;
      trackPageView(pathname);
    }
  }, [pathname]);

  return <>{children}</>;
}
