"use client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Generate a unique visitor ID and store it in localStorage
function getVisitorId(): string {
  if (typeof window === "undefined") return "";

  let visitorId = localStorage.getItem("ot_visitor_id");
  if (!visitorId) {
    visitorId = crypto.randomUUID();
    localStorage.setItem("ot_visitor_id", visitorId);
  }
  return visitorId;
}

// Track a page view
export async function trackPageView(path: string): Promise<void> {
  try {
    const visitorId = getVisitorId();
    const referrer = document.referrer || null;

    await fetch(`${API_URL}/api/v1/analytics/track`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        path,
        referrer,
        visitor_id: visitorId,
      }),
    });
  } catch (error) {
    // Silently fail - analytics should not break the app
    console.debug("Analytics tracking failed:", error);
  }
}
