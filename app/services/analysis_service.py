"""Analysis orchestration service tying together extraction, caching, and LLM processing."""

import logging
import time
from typing import Dict, Optional, Tuple
from app.config import settings
from app.schemas import LinkAnalysisResponse, AnalysisMetadata
from app.services.competitor_service import CompetitorService
from app.services.llm_service import LLMService
from app.services.website_extractor import WebsiteExtractor, WebsiteExtractionError
from app.utils.validators import validate_and_sanitize_url

logger = logging.getLogger(__name__)


class CacheEntry:
    """In-memory cache entry with TTL."""
    def __init__(self, response: LinkAnalysisResponse, ttl_seconds: int):
        self.response = response
        self.expires_at = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class AnalysisService:
    """High-level service orchestrating link extraction, caching, intelligence analysis, and response generation."""

    def __init__(self):
        self.extractor = WebsiteExtractor()
        self.llm_service = LLMService()
        self.competitor_service = CompetitorService()
        self._cache: Dict[str, CacheEntry] = {}

    async def analyze_url(self, raw_url: str) -> LinkAnalysisResponse:
        """
        Execute end-to-end website link analysis.
        
        1. Validates URL and prevents SSRF.
        2. Checks response cache to save tokens and latency.
        3. Scrapes and parses website structure.
        4. Analyzes with LLM for business, competitor, SEO, search query, and audience insights.
        5. Validates and returns structured JSON response.
        """
        start_time = time.perf_counter()
        safe_url = validate_and_sanitize_url(raw_url)

        # 1. Cache lookup
        if settings.ENABLE_CACHE and safe_url in self._cache:
            entry = self._cache[safe_url]
            if not entry.is_expired():
                logger.info(f"Serving cached analysis for {safe_url}")
                cached_resp = entry.response.model_copy(deep=True)
                if cached_resp.metadata:
                    cached_resp.metadata.cached = True
                    cached_resp.metadata.processing_time_seconds = round(time.perf_counter() - start_time, 4)
                return cached_resp
            else:
                del self._cache[safe_url]

        # 2. Extract website content
        extracted_data = await self.extractor.fetch_and_extract(safe_url)

        # 3. LLM analysis
        brand_summary, analysis_payload, meta_dict = await self.llm_service.analyze_website(extracted_data)

        # 4. Enrich competitor matrix if needed
        comp_section = analysis_payload.competitor_analysis
        if not comp_section.comparison_table and comp_section.competitors:
            comp_section.comparison_table = self.competitor_service.build_comparison_matrix(
                brand_name=brand_summary.name,
                category=brand_summary.category,
                brand_strengths=comp_section.strengths,
                primary_competitor=comp_section.competitors[0]
            )

        total_time = round(time.perf_counter() - start_time, 2)
        meta_dict["processing_time_seconds"] = total_time

        # 5. Build final response
        response = LinkAnalysisResponse(
            success=True,
            website=safe_url,
            brand=brand_summary,
            analysis=analysis_payload,
            metadata=AnalysisMetadata(**meta_dict)
        )

        # 6. Store in cache
        if settings.ENABLE_CACHE:
            self._cache[safe_url] = CacheEntry(response, settings.CACHE_TTL_SECONDS)

        return response
