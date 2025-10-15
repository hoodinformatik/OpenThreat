"""
LLM Service for generating user-friendly CVE titles and descriptions.

Uses Ollama with a local LLM (e.g., Llama 3.2, Mistral) to process CVE data
and generate plain-language summaries.
"""
import logging
from typing import Optional, Dict
import ollama
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating CVE summaries using local LLM."""
    
    def __init__(self, model: str = "llama3.2:3b", enabled: bool = True):
        """
        Initialize LLM service.
        
        Args:
            model: Ollama model to use (default: llama3.2:3b)
            enabled: Whether LLM processing is enabled
        """
        self.model = model
        self.enabled = enabled
        
        if enabled:
            try:
                # Test if Ollama is available
                ollama.list()
                logger.info(f"LLM Service initialized with model: {model}")
            except Exception as e:
                logger.warning(f"Ollama not available: {e}. LLM features disabled.")
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
        if not self.enabled:
            # Fallback to original data if LLM is disabled
            return {
                "simple_title": original_title or cve_id,
                "simple_description": description[:200] + "..." if len(description) > 200 else description
            }
        
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
            title_response = ollama.generate(
                model=self.model,
                prompt=title_prompt,
                options={
                    "temperature": 0.3,  # Low temperature for consistency
                    "num_predict": 50,   # Short response
                }
            )
            simple_title = title_response['response'].strip()
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
            desc_response = ollama.generate(
                model=self.model,
                prompt=desc_prompt,
                options={
                    "temperature": 0.4,
                    "num_predict": 150,
                }
            )
            simple_description = desc_response['response'].strip()
            # Remove quotes if present
            simple_description = simple_description.strip('"').strip("'").strip()
            
            # Remove common LLM meta-text patterns
            simple_description = self._clean_description(simple_description)
            
            logger.info(f"Generated summary for {cve_id}")
            
            return {
                "simple_title": simple_title,
                "simple_description": simple_description
            }
            
        except Exception as e:
            logger.error(f"Error generating summary for {cve_id}: {e}")
            # Fallback to original data
            return {
                "simple_title": original_title or cve_id,
                "simple_description": description[:200] + "..." if len(description) > 200 else description
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
        self,
        vulnerabilities: list,
        max_batch_size: int = 10
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
            cve_id = vuln.get('cve_id')
            if not cve_id:
                continue
                
            summary = self.generate_cve_summary(
                cve_id=cve_id,
                original_title=vuln.get('title'),
                description=vuln.get('description', ''),
                cvss_score=vuln.get('cvss_score'),
                severity=vuln.get('severity'),
                vendors=vuln.get('vendors', []),
                products=vuln.get('products', []),
                published_at=vuln.get('published_at')
            )
            
            results[cve_id] = summary
        
        return results


# Global instance
_llm_service = None


def get_llm_service(model: str = "llama3.2:3b", enabled: bool = True) -> LLMService:
    """Get or create global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(model=model, enabled=enabled)
    return _llm_service
