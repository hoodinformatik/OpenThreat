/**
 * Plain-language explanations for technical security terms
 * Making threat intelligence accessible to everyone
 */

export interface Explanation {
  title: string;
  simple: string;
  whatItMeans: string;
  whatToDo: string;
  urgency: "critical" | "high" | "medium" | "low";
}

/**
 * Generate plain-language explanation for severity levels
 */
export function explainSeverity(severity: string | null | undefined): Explanation {
  const sev = severity?.toUpperCase();

  switch (sev) {
    case "CRITICAL":
      return {
        title: "Critical Severity",
        simple: "This is an extremely serious security vulnerability.",
        whatItMeans:
          "Attackers can easily exploit this vulnerability to take complete control of affected systems, steal sensitive data, or cause major disruptions. No user interaction is typically required.",
        whatToDo:
          "⚠️ Act immediately! Apply security patches within 24-48 hours. If patches aren't available, consider taking affected systems offline or implementing emergency workarounds.",
        urgency: "critical",
      };

    case "HIGH":
      return {
        title: "High Severity",
        simple: "This is a serious security vulnerability that needs prompt attention.",
        whatItMeans:
          "Attackers can exploit this to gain unauthorized access, steal data, or disrupt services. It may require some user interaction (like clicking a link) but is still dangerous.",
        whatToDo:
          "⚠️ Prioritize patching within 1-2 weeks. Review affected systems and plan updates. Monitor for exploitation attempts.",
        urgency: "high",
      };

    case "MEDIUM":
      return {
        title: "Medium Severity",
        simple: "This vulnerability poses a moderate security risk.",
        whatItMeans:
          "Attackers need specific conditions or user actions to exploit this. It could lead to information disclosure or limited system access.",
        whatToDo:
          "📋 Plan to patch within 30 days. Include in your regular update cycle. Not urgent but shouldn't be ignored.",
        urgency: "medium",
      };

    case "LOW":
      return {
        title: "Low Severity",
        simple: "This is a minor security issue with limited impact.",
        whatItMeans:
          "Exploitation is difficult and would have minimal impact. Often requires very specific conditions or provides very limited access.",
        whatToDo:
          "📝 Address during routine maintenance. Can be included in regular update schedules without urgency.",
        urgency: "low",
      };

    default:
      return {
        title: "Unknown Severity",
        simple: "The severity of this vulnerability hasn't been determined yet.",
        whatItMeans:
          "This vulnerability is still being analyzed. The risk level is not yet clear.",
        whatToDo:
          "⏳ Monitor for updates. Check back later for severity assessment and recommendations.",
        urgency: "medium",
      };
  }
}

/**
 * Explain CVSS scores in plain language
 */
export function explainCVSS(score: number | null | undefined): string {
  if (!score) return "No CVSS score available yet.";

  if (score >= 9.0) {
    return `Score ${score}/10 - Extremely dangerous. This vulnerability is very easy to exploit and has severe consequences.`;
  } else if (score >= 7.0) {
    return `Score ${score}/10 - Highly dangerous. This vulnerability can be exploited with moderate effort and has serious impact.`;
  } else if (score >= 4.0) {
    return `Score ${score}/10 - Moderately dangerous. Exploitation requires some effort or specific conditions.`;
  } else {
    return `Score ${score}/10 - Low danger. Exploitation is difficult and impact is limited.`;
  }
}

/**
 * Explain exploitation status
 */
export function explainExploitation(exploited: boolean): Explanation {
  if (exploited) {
    return {
      title: "⚠️ Actively Exploited in the Wild",
      simple: "Hackers are already using this vulnerability to attack systems right now.",
      whatItMeans:
        "This isn't theoretical - real attacks are happening. Cybercriminals have working exploit code and are actively targeting vulnerable systems. Your organization could be attacked at any moment if you're vulnerable.",
      whatToDo:
        "🚨 URGENT: Patch immediately! This is a top priority. Check if your systems are affected and apply updates as soon as possible. Consider this a security emergency.",
      urgency: "critical",
    };
  } else {
    return {
      title: "Not Currently Exploited",
      simple: "No active attacks using this vulnerability have been detected yet.",
      whatItMeans:
        "While this vulnerability exists, there's no evidence of hackers actively using it in real-world attacks. However, this could change at any time.",
      whatToDo:
        "📋 Follow the severity-based timeline for patching. Stay alert for updates about exploitation status.",
      urgency: "medium",
    };
  }
}

/**
 * Explain CWE (Common Weakness Enumeration)
 */
export function explainCWE(cweId: string): string {
  const cweMap: Record<string, string> = {
    "CWE-79": "Cross-Site Scripting (XSS) - Attackers can inject malicious code into websites that runs in victims' browsers.",
    "CWE-89": "SQL Injection - Attackers can manipulate database queries to steal or modify data.",
    "CWE-20": "Improper Input Validation - The software doesn't properly check user input, allowing malicious data.",
    "CWE-78": "OS Command Injection - Attackers can execute system commands on the server.",
    "CWE-22": "Path Traversal - Attackers can access files they shouldn't be able to reach.",
    "CWE-352": "Cross-Site Request Forgery (CSRF) - Attackers can trick users into performing unwanted actions.",
    "CWE-434": "Unrestricted File Upload - Attackers can upload malicious files to the system.",
    "CWE-94": "Code Injection - Attackers can inject and execute their own code.",
    "CWE-287": "Improper Authentication - Weak login/authentication mechanisms that can be bypassed.",
    "CWE-798": "Hard-coded Credentials - Passwords or keys are embedded in the code and can't be changed easily.",
  };

  return cweMap[cweId] || `${cweId} - A specific type of security weakness. Check CWE database for details.`;
}

/**
 * Generate action recommendations based on vulnerability characteristics
 */
export function generateActionPlan(vuln: {
  severity?: string;
  exploited_in_the_wild: boolean;
  cvss_score?: number;
  cisa_due_date?: string;
}): {
  priority: string;
  timeline: string;
  steps: string[];
} {
  const isExploited = vuln.exploited_in_the_wild;
  const isCritical = vuln.severity === "CRITICAL" || (vuln.cvss_score && vuln.cvss_score >= 9.0);
  const hasCISADeadline = !!vuln.cisa_due_date;

  if (isExploited || hasCISADeadline) {
    return {
      priority: "🚨 URGENT - Act Immediately",
      timeline: hasCISADeadline
        ? `CISA requires action by ${new Date(vuln.cisa_due_date!).toLocaleDateString()}`
        : "Within 24-48 hours",
      steps: [
        "1. Identify all affected systems in your organization",
        "2. Check vendor websites for security patches",
        "3. Test patches in a non-production environment if possible",
        "4. Deploy patches to production systems immediately",
        "5. If no patch exists, implement temporary workarounds or isolate affected systems",
        "6. Monitor systems for signs of compromise",
        "7. Document all actions taken",
      ],
    };
  }

  if (isCritical) {
    return {
      priority: "⚠️ HIGH PRIORITY",
      timeline: "Within 1-2 weeks",
      steps: [
        "1. Inventory affected systems and software versions",
        "2. Download and review available security patches",
        "3. Schedule maintenance window for patching",
        "4. Test patches in development/staging environment",
        "5. Deploy to production during scheduled maintenance",
        "6. Verify patches were applied successfully",
        "7. Update documentation and asset inventory",
      ],
    };
  }

  if (vuln.severity === "HIGH") {
    return {
      priority: "📋 Medium Priority",
      timeline: "Within 30 days",
      steps: [
        "1. Add to your regular patching schedule",
        "2. Review affected systems and plan updates",
        "3. Test patches when convenient",
        "4. Deploy during next maintenance window",
        "5. Verify successful deployment",
      ],
    };
  }

  return {
    priority: "📝 Low Priority",
    timeline: "Next regular update cycle (60-90 days)",
    steps: [
      "1. Include in routine maintenance",
      "2. Batch with other low-priority updates",
      "3. Deploy during regular update schedule",
      "4. Document completion",
    ],
  };
}

/**
 * Explain what a CVE is for non-technical users
 */
export function explainCVE(): string {
  return `A CVE (Common Vulnerabilities and Exposures) is like a unique ID number for a security bug. 
  When security researchers discover a vulnerability in software, it gets assigned a CVE number 
  (like CVE-2024-1234) so everyone can talk about the same issue. Think of it as a tracking number 
  for security problems.`;
}

/**
 * Explain priority score
 */
export function explainPriorityScore(score: number | null | undefined): string {
  if (!score) return "Priority score not available.";

  const percentage = (score * 100).toFixed(0);

  if (score >= 0.8) {
    return `${percentage}% priority - Extremely urgent. This combines high severity, active exploitation, and recent discovery.`;
  } else if (score >= 0.6) {
    return `${percentage}% priority - High priority. Significant risk that should be addressed soon.`;
  } else if (score >= 0.4) {
    return `${percentage}% priority - Medium priority. Important but not urgent.`;
  } else {
    return `${percentage}% priority - Lower priority. Can be addressed in regular maintenance.`;
  }
}
