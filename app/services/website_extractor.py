"""Website content extraction and cleaning service using HTTPX and BeautifulSoup."""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.utils.validators import validate_and_sanitize_url, URLValidationError

logger = logging.getLogger(__name__)


class WebsiteExtractionError(Exception):
    """Raised when website cannot be fetched or parsed."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class ExtractedWebsiteData:
    """Structured container for cleaned website content and metadata."""
    url: str
    final_url: str
    domain: str
    title: str
    meta_description: str
    meta_keywords: List[str] = field(default_factory=list)
    og_site_name: Optional[str] = None
    inferred_brand_name: Optional[str] = None
    headings_h1: List[str] = field(default_factory=list)
    headings_h2: List[str] = field(default_factory=list)
    headings_h3: List[str] = field(default_factory=list)
    navigation_links: List[str] = field(default_factory=list)
    key_paragraphs: List[str] = field(default_factory=list)
    schema_org_data: List[Dict] = field(default_factory=list)
    cleaned_body_text: str = ""

    def to_llm_prompt_context(self, max_length: int = settings.MAX_CONTENT_LENGTH) -> str:
        """
        Produce a compact, high-signal text representation optimized for LLM token usage.
        Avoids redundant HTML markup while prioritizing brand and business data.
        """
        lines = [
            f"=== WEBSITE CONTEXT ===",
            f"Target URL: {self.final_url}",
            f"Domain: {self.domain}",
            f"Page Title: {self.title}",
            f"Meta Description: {self.meta_description or 'None provided'}",
        ]

        if self.inferred_brand_name:
            lines.append(f"Detected Brand Name: {self.inferred_brand_name}")

        if self.meta_keywords:
            lines.append(f"Meta Keywords: {', '.join(self.meta_keywords[:15])}")

        if self.headings_h1:
            lines.append(f"Main Headings (H1): {' | '.join(self.headings_h1[:5])}")

        if self.headings_h2:
            lines.append(f"Section Headings (H2): {' | '.join(self.headings_h2[:12])}")

        if self.headings_h3:
            lines.append(f"Sub-Headings (H3): {' | '.join(self.headings_h3[:12])}")

        if self.navigation_links:
            lines.append(f"Navigation/Service Links: {', '.join(self.navigation_links[:20])}")

        if self.schema_org_data:
            compact_schema = json.dumps(self.schema_org_data[:3], ensure_ascii=False)
            lines.append(f"Schema.org Data: {compact_schema[:1000]}")

        lines.append("\n=== MAIN PAGE BODY CONTENT ===")
        # Truncate cleaned body text to stay strictly within max_length
        budget = max(500, max_length - len("\n".join(lines)))
        lines.append(self.cleaned_body_text[:budget])

        return "\n".join(lines)


class WebsiteExtractor:
    """Fetches and extracts clean, structured content from a target website."""

    def __init__(self, timeout: int = settings.REQUEST_TIMEOUT):
        self.timeout = timeout
        self.headers = {
            "User-Agent": settings.SCRAPER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1",
        }

    async def fetch_and_extract(self, url: str) -> ExtractedWebsiteData:
        """
        Validate URL, fetch HTML content asynchronously, and parse relevant content.
        
        Args:
            url: Validated public website URL
            
        Returns:
            ExtractedWebsiteData object
            
        Raises:
            WebsiteExtractionError: For network or parsing issues
        """
        safe_url = validate_and_sanitize_url(url)
        final_url = safe_url

        try:
            async with httpx.AsyncClient(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=5,
                verify=True
            ) as client:
                response = await client.get(safe_url)
                final_url = str(response.url)

                # Re-validate final URL in case a redirect went to an internal or disallowed host
                try:
                    validate_and_sanitize_url(final_url)
                except URLValidationError as err:
                    raise WebsiteExtractionError(f"Redirected to forbidden address: {str(err)}", status_code=400)

                if response.status_code >= 400:
                    raise WebsiteExtractionError(
                        f"Website returned HTTP {response.status_code} ({response.reason_phrase})",
                        status_code=response.status_code
                    )

                html_content = response.text

        except httpx.TimeoutException:
            raise WebsiteExtractionError(f"Connection timed out after {self.timeout}s while fetching {url}", status_code=504)
        except httpx.ConnectError as err:
            raise WebsiteExtractionError(f"Failed to connect to host: {str(err)}", status_code=502)
        except httpx.HTTPError as err:
            raise WebsiteExtractionError(f"HTTP request error: {str(err)}", status_code=502)
        except WebsiteExtractionError:
            raise
        except Exception as err:
            raise WebsiteExtractionError(f"Unexpected error fetching website: {str(err)}", status_code=500)

        return self.parse_html(html_content, target_url=safe_url, final_url=final_url)

    def parse_html(self, html: str, target_url: str, final_url: str) -> ExtractedWebsiteData:
        """Parse raw HTML and extract brand, SEO, heading, and text signals."""
        soup = BeautifulSoup(html, "html.parser")
        parsed_url = urlparse(final_url)
        domain = parsed_url.netloc or parsed_url.hostname or ""

        # 1. Page Title
        title = ""
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
        elif soup.find("meta", property="og:title"):
            title = soup.find("meta", property="og:title").get("content", "").strip()

        # 2. Meta Description
        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()
        elif soup.find("meta", property="og:description"):
            meta_desc = soup.find("meta", property="og:description").get("content", "").strip()

        # 3. Meta Keywords
        keywords: List[str] = []
        kw_tag = soup.find("meta", attrs={"name": re.compile(r"^keywords$", re.I)})
        if kw_tag and kw_tag.get("content"):
            raw_kws = kw_tag["content"].split(",")
            keywords = [k.strip() for k in raw_kws if k.strip()]

        # 4. OpenGraph Site Name & Brand Inference
        og_site_name = None
        og_site_tag = soup.find("meta", property="og:site_name")
        if og_site_tag and og_site_tag.get("content"):
            og_site_name = og_site_tag["content"].strip()

        inferred_brand = og_site_name
        if not inferred_brand and title:
            # Common pattern: "Page Name | Brand Name" or "Brand Name - Tagline"
            parts = re.split(r"[\s\-_|:•~»]+", title)
            if parts:
                inferred_brand = parts[-1].strip() if len(parts[-1].strip()) > 2 else parts[0].strip()

        if not inferred_brand:
            # Fallback to domain name without TLD
            domain_parts = domain.replace("www.", "").split(".")
            inferred_brand = domain_parts[0].capitalize() if domain_parts else domain

        # 5. Schema.org JSON-LD
        schemas: List[Dict] = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                if script.string:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        schemas.append(data)
                    elif isinstance(data, list):
                        schemas.extend([item for item in data if isinstance(item, dict)])
            except Exception:
                continue

        # 6. Headings
        h1s = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
        h2s = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]
        h3s = [h.get_text(strip=True) for h in soup.find_all("h3") if h.get_text(strip=True)]

        # 7. Navigation & Service Links
        nav_links: List[str] = []
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            if 3 <= len(text) <= 40 and text not in nav_links:
                href_lower = a["href"].lower()
                if any(k in href_lower for k in ["service", "product", "solution", "about", "pricing", "feature", "industry"]):
                    nav_links.append(text)

        # 8. Clean Body Text (Strip noise: scripts, styles, forms, svgs, footers, etc.)
        for tag in soup(["script", "style", "noscript", "svg", "iframe", "form"]):
            tag.decompose()

        # Collect paragraphs
        paragraphs = []
        for p in soup.find_all(["p", "li"]):
            text = p.get_text(separator=" ", strip=True)
            # Filter out single words or very short fragments
            if len(text.split()) >= 4:
                paragraphs.append(text)

        raw_text = soup.get_text(separator="\n", strip=True)
        # Collapse multiple whitespace and consecutive empty lines
        cleaned_lines = [re.sub(r"\s+", " ", line).strip() for line in raw_text.splitlines() if line.strip()]
        cleaned_text = "\n".join(cleaned_lines)

        return ExtractedWebsiteData(
            url=target_url,
            final_url=final_url,
            domain=domain,
            title=title,
            meta_description=meta_desc,
            meta_keywords=keywords,
            og_site_name=og_site_name,
            inferred_brand_name=inferred_brand,
            headings_h1=h1s[:10],
            headings_h2=h2s[:20],
            headings_h3=h3s[:20],
            navigation_links=nav_links[:30],
            key_paragraphs=paragraphs[:25],
            schema_org_data=schemas[:5],
            cleaned_body_text=cleaned_text
        )
