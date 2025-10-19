"""
LLM Service for generating user-friendly CVE titles and descriptions.

Uses Ollama with a local LLM (e.g., Llama 3.2, Mistral) to process CVE data
and generate plain-language summaries.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Optional

import ollama

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating CVE summaries using local LLM."""

    def __init__(self, model: str = None, enabled: bool = True):
        """
        Initialize LLM service.

        Args:
            model: Ollama model to use (default: from LLM_MODEL env or llama3.2:1b)
            enabled: Whether LLM processing is enabled
        """
        # Get model from env or use provided model or default
        self.model = model or os.getenv("LLM_MODEL", "llama3.2:1b")
        self.enabled = enabled
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        # Configure Ollama client
        self.client = ollama.Client(host=self.ollama_host)

        if enabled:
            try:
                # Test if Ollama is available
                self.client.list()
                logger.info(
                    f"LLM Service initialized with model: {self.model} at {self.ollama_host}"
                )
            except Exception as e:
                logger.warning(
                    f"Ollama not available at {self.ollama_host}: {e}. LLM features disabled."
                )
                self.enabled = False

    def generate_cve_summary(
        self,
        cve_id: str,
        original_title: str,
        description: str,
        cvss_score: Optional[float] = None,
        severity: Optional[str] = None,
        vendors: Optional[list] = None,
        products: Optional[list] = None,
        published_at: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """
        Generate user-friendly title and description for a CVE.

        Args:
            cve_id: CVE identifier
            original_title: Original CVE title
            description: Technical CVE description
            cvss_score: CVSS score (0-10)
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
            vendors: List of affected vendors
            products: List of affected products
            published_at: Publication date

        Returns:
            Dict with 'simple_title' and 'simple_description'
        """
        # Use LLM-based generation
        return self.generate_cve_summary_with_llm(
            cve_id,
            original_title,
            description,
            cvss_score,
            severity,
            vendors,
            products,
            published_at,
        )

    def _generate_simple_summary(
        self,
        cve_id: str,
        original_title: str,
        description: str,
        cvss_score: Optional[float],
        severity: Optional[str],
        vendors: Optional[list],
        products: Optional[list],
        published_at: Optional[datetime],
    ) -> Dict[str, str]:
        """Generate simple title and description without LLM (rule-based)."""

        # Build simple title
        vendor_str = vendors[0] if vendors and len(vendors) > 0 else "Unknown"
        product_str = products[0] if products and len(products) > 0 else "Software"

        # Extract vulnerability type from description
        vuln_type = "Vulnerability"
        desc_lower = description.lower() if description else ""

        if "remote code execution" in desc_lower or "rce" in desc_lower:
            vuln_type = "Remote Code Execution"
        elif "sql injection" in desc_lower:
            vuln_type = "SQL Injection"
        elif "cross-site scripting" in desc_lower or "xss" in desc_lower:
            vuln_type = "Cross-Site Scripting"
        elif "buffer overflow" in desc_lower:
            vuln_type = "Buffer Overflow"
        elif "denial of service" in desc_lower or "dos" in desc_lower:
            vuln_type = "Denial of Service"
        elif "authentication" in desc_lower or "bypass" in desc_lower:
            vuln_type = "Authentication Bypass"
        elif "privilege escalation" in desc_lower:
            vuln_type = "Privilege Escalation"
        elif "information disclosure" in desc_lower:
            vuln_type = "Information Disclosure"
        elif "path traversal" in desc_lower or "directory traversal" in desc_lower:
            vuln_type = "Path Traversal"
        elif "command injection" in desc_lower:
            vuln_type = "Command Injection"

        # Create simple title
        simple_title = f"{vuln_type} in {vendor_str} {product_str}"
        if severity:
            simple_title = f"{severity.title()} {simple_title}"

        # Limit title length
        if len(simple_title) > 100:
            simple_title = simple_title[:97] + "..."

        # Create simple description (first 2-3 sentences)
        simple_description = (
            description[:300] if description else "No description available."
        )

        # Try to end at sentence boundary
        if len(description) > 300:
            last_period = simple_description.rfind(".")
            if last_period > 100:
                simple_description = simple_description[: last_period + 1]
            else:
                simple_description += "..."

        return {"simple_title": simple_title, "simple_description": simple_description}

    def generate_cve_summary_with_llm(
        self,
        cve_id: str,
        original_title: str,
        description: str,
        cvss_score: Optional[float] = None,
        severity: Optional[str] = None,
        vendors: Optional[list] = None,
        products: Optional[list] = None,
        published_at: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """
        Generate summary using LLM (slow, only use if you have GPU).
        This is the original LLM-based implementation.
        """
        if not self.enabled:
            # Fallback to rule-based
            return self._generate_simple_summary(
                cve_id,
                original_title,
                description,
                cvss_score,
                severity,
                vendors,
                products,
                published_at,
            )

        try:
            # Build context
            vendor_str = ", ".join(vendors[:3]) if vendors else "Unknown"
            product_str = ", ".join(products[:3]) if products else "Unknown"
            date_str = published_at.strftime("%Y-%m-%d") if published_at else "Unknown"

            # Prompt for title generation
            title_prompt = f"""You are a cybersecurity expert explaining vulnerabilities to non-technical users.

CVE ID: {cve_id}
Affected Vendor: {vendor_str}
Affected Product: {product_str}
Severity: {severity or 'Unknown'}
CVSS Score: {cvss_score or 'Unknown'}

Technical Description:
{description[:500]}

Generate a SHORT, simple title (maximum 10 words) that describes:
1. What the vulnerability is (in simple terms)
2. Where it affects (vendor/product)

Example format: "Security Flaw in Microsoft Windows Allows Remote Access"

Generate ONLY the title, nothing else:"""

            # Generate title
            title_response = self.client.generate(
                model=self.model,
                prompt=title_prompt,
                options={
                    "temperature": 0.3,  # Low temperature for consistency
                    "num_predict": 50,  # Short response
                },
            )
            simple_title = title_response["response"].strip()
            # Remove quotes if present
            simple_title = simple_title.strip('"').strip("'").strip()

            # Prompt for description generation
            desc_prompt = f"""You are a cybersecurity expert explaining vulnerabilities to non-technical users.

CVE ID: {cve_id}
Date: {date_str}
Severity: {severity or 'Unknown'}
CVSS Score: {cvss_score or 'Unknown'}/10
Affected: {vendor_str} {product_str}

Technical Description:
{description[:800]}

Write a BRIEF, simple explanation (2-3 sentences, maximum 100 words) that:
1. Explains what the vulnerability is in plain language
2. Describes the potential impact
3. Avoids technical jargon

IMPORTANT: Start directly with the explanation. Do NOT use phrases like "Here's a brief explanation" or "In simple terms". Just write the description.

Example good output: "This vulnerability allows attackers to remotely access Windows systems without authentication. It affects all Windows 10 and 11 versions. Microsoft has released a security update to fix this issue."

Generate ONLY the description:"""

            # Generate description
            desc_response = self.client.generate(
                model=self.model,
                prompt=desc_prompt,
                options={
                    "temperature": 0.4,
                    "num_predict": 150,
                },
            )
            simple_description = desc_response["response"].strip()
            # Remove quotes if present
            simple_description = simple_description.strip('"').strip("'").strip()

            # Remove common LLM meta-text patterns
            simple_description = self._clean_description(simple_description)

            logger.info(f"Generated summary for {cve_id}")

            return {
                "simple_title": simple_title,
                "simple_description": simple_description,
            }

        except Exception as e:
            logger.error(f"Error generating summary for {cve_id}: {e}")
            # Fallback to original data
            return {
                "simple_title": original_title or cve_id,
                "simple_description": (
                    description[:200] + "..." if len(description) > 200 else description
                ),
            }

    def _clean_description(self, text: str) -> str:
        """
        Remove common LLM meta-text patterns from descriptions.

        Args:
            text: Raw LLM output

        Returns:
            Cleaned description
        """
        import re

        # Patterns to remove (case-insensitive)
        patterns = [
            r"^here'?s?\s+a\s+brief\s+explanation\s+of\s+the\s+vulnerability:?\s*",
            r"^here'?s?\s+a\s+brief\s+summary:?\s*",
            r"^here'?s?\s+what\s+you\s+need\s+to\s+know:?\s*",
            r"^in\s+simple\s+terms:?\s*",
            r"^to\s+put\s+it\s+simply:?\s*",
            r"^basically,?\s*",
            r"^essentially,?\s*",
            r"^in\s+other\s+words,?\s*",
        ]

        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # Remove leading/trailing whitespace and capitalize first letter
        cleaned = cleaned.strip()
        if cleaned and cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]

        return cleaned

    def batch_generate_summaries(
        self, vulnerabilities: list, max_batch_size: int = 10
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate summaries for multiple CVEs in batch.

        Args:
            vulnerabilities: List of vulnerability dicts
            max_batch_size: Maximum number to process in one batch

        Returns:
            Dict mapping CVE IDs to summaries
        """
        results = {}

        for vuln in vulnerabilities[:max_batch_size]:
            cve_id = vuln.get("cve_id")
            if not cve_id:
                continue

            summary = self.generate_cve_summary(
                cve_id=cve_id,
                original_title=vuln.get("title"),
                description=vuln.get("description", ""),
                cvss_score=vuln.get("cvss_score"),
                severity=vuln.get("severity"),
                vendors=vuln.get("vendors", []),
                products=vuln.get("products", []),
                published_at=vuln.get("published_at"),
            )

            results[cve_id] = summary

        return results


# Global instance
_llm_service = None


def get_llm_service(model: str = None, enabled: bool = True) -> LLMService:
    """Get or create global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(model=model, enabled=enabled)
    return _llm_service
