"""Competitor intelligence service for enrichment, comparison, and verification."""

import logging
from typing import Dict, List, Optional
from app.schemas import BrandComparisonItem, CompetitorDetail

logger = logging.getLogger(__name__)


class CompetitorService:
    """Specialized service for competitor benchmarking and positioning logic."""

    @staticmethod
    def build_comparison_matrix(
        brand_name: str,
        category: str,
        brand_strengths: List[str],
        primary_competitor: CompetitorDetail
    ) -> List[BrandComparisonItem]:
        """Generate structured comparison rows between your brand and the primary competitor."""
        brand_strength_summary = brand_strengths[0] if brand_strengths else "Agile specialized delivery"
        comp_strength_summary = primary_competitor.strengths[0] if primary_competitor.strengths else "Established market presence"

        return [
            BrandComparisonItem(
                criteria="Brand Name",
                your_brand=brand_name,
                competitor=primary_competitor.name
            ),
            BrandComparisonItem(
                criteria="Main Category / Focus",
                your_brand=category,
                competitor=primary_competitor.category
            ),
            BrandComparisonItem(
                criteria="Market Overlap",
                your_brand="Targeted High-Touch Engagements",
                competitor=primary_competitor.market_overlap
            ),
            BrandComparisonItem(
                criteria="Key Strength",
                your_brand=brand_strength_summary,
                competitor=comp_strength_summary
            ),
            BrandComparisonItem(
                criteria="Identified Gap / Advantage",
                your_brand="Rapid custom iteration & lower overhead",
                competitor=primary_competitor.weaknesses_or_gaps[0] if primary_competitor.weaknesses_or_gaps else "Higher legacy pricing"
            )
        ]
