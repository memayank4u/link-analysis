"""Pydantic data models for the Website Link Analysis API."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl


class LinkAnalysisRequest(BaseModel):
    """Incoming request model for website analysis."""
    url: str = Field(
        ...,
        description="Publicly accessible website URL to analyze",
        examples=["https://example.com"]
    )


# -------------------------------------------------------------
# Section 1: Competitor vs Your Brand Details
# -------------------------------------------------------------

class CompetitorDetail(BaseModel):
    """Individual competitor analysis details."""
    name: str = Field(..., description="Competitor brand name")
    category: str = Field(..., description="Primary business category")
    strengths: List[str] = Field(default_factory=list, description="Key competitor strengths")
    weaknesses_or_gaps: List[str] = Field(default_factory=list, description="Competitor weaknesses or market gaps")
    market_overlap: str = Field(..., description="Nature of overlap with your brand")


class BrandComparisonItem(BaseModel):
    """Row in brand vs competitor comparison table."""
    criteria: str = Field(..., description="Comparison dimension (e.g. Main Service, Target Market, Key Strength)")
    your_brand: str = Field(..., description="Your brand's position")
    competitor: str = Field(..., description="Competitor's position")


class CompetitorAnalysisSection(BaseModel):
    """Section 1: Competitor vs Your Brand Details."""
    brand_overview: str = Field(..., description="Comprehensive overview of your brand")
    main_business_category: str = Field(..., description="Main business category")
    main_products_and_services: List[str] = Field(default_factory=list, description="Key offerings")
    competitors: List[CompetitorDetail] = Field(
        ...,
        min_length=3,
        description="Identified competitors (minimum 3 where reliable information is available)"
    )
    strengths: List[str] = Field(default_factory=list, description="Your brand's competitive advantages")
    opportunities: List[str] = Field(default_factory=list, description="Opportunities to improve market positioning")
    comparison_table: List[BrandComparisonItem] = Field(
        default_factory=list,
        description="Structured comparison table between your brand and key competitors"
    )


# -------------------------------------------------------------
# Section 2: Top 5 Target Search Queries
# -------------------------------------------------------------

class TargetSearchQuery(BaseModel):
    """Individual target search query across platforms."""
    query: str = Field(..., description="Recommended search query phrase")
    platforms: List[str] = Field(
        ...,
        description="Supported platforms where query is relevant (Google, Facebook, Instagram, LinkedIn, X)"
    )
    intent: str = Field(..., description="Search intent (e.g., Service Search, Business Discovery, B2B Search, Inspiration)")
    business_relevance: str = Field(..., description="Why this query matters for the business")
    target_audience: str = Field(..., description="Specific audience segment using this query")
    data_source_note: str = Field(
        default="Qualitative AI intent mapping; search volumes require third-party search APIs",
        description="Data verification note regarding search volume honesty"
    )


# -------------------------------------------------------------
# Section 3: SEO Improvement
# -------------------------------------------------------------

class SupportingContentItem(BaseModel):
    """Suggested content addition for SEO enhancement."""
    type: str = Field(..., description="Content type (Service landing page, Industry page, FAQ, Blog topic, etc.)")
    topic: str = Field(..., description="Recommended title or topic")
    rationale: str = Field(..., description="Why this content improves search visibility")


class SEOImprovementsSection(BaseModel):
    """Section 3: SEO Improvements."""
    # A. Keyword Recommendations
    primary_keyword: str = Field(..., description="Main primary focus keyword")
    secondary_keywords: List[str] = Field(default_factory=list, description="Secondary focus keywords")
    long_tail_keywords: List[str] = Field(default_factory=list, description="High-intent long-tail keywords")
    relevant_business_keywords: List[str] = Field(default_factory=list, description="Industry and business-relevant keywords")

    # B. SEO Title
    recommended_title: str = Field(..., description="Recommended SEO title (< 60 chars)")
    title_primary_keyword: str = Field(..., description="Primary keyword included in title")
    title_structure_explanation: str = Field(..., description="Improved title structure explanation")

    # C. Meta Description
    meta_description: str = Field(..., description="Recommended meta description (< 160 chars)")
    meta_summary: str = Field(..., description="Short, human-friendly business summary")
    meta_keywords_used: List[str] = Field(default_factory=list, description="Keywords incorporated in meta description")

    # D. Supporting Content
    supporting_content: List[SupportingContentItem] = Field(
        default_factory=list,
        description="Strategic supporting content recommendations"
    )


# -------------------------------------------------------------
# Section 4: Top 5 Services
# -------------------------------------------------------------

class ServiceItem(BaseModel):
    """Section 4: Service detail."""
    service_name: str = Field(..., description="Name of the service")
    description: str = Field(..., description="Short service explanation")
    target_industry: str = Field(..., description="Relevant business industry")
    target_customer: str = Field(..., description="Potential customer type")
    main_benefit: str = Field(..., description="Why customers need this service")
    source: Literal["actual_content", "inferred"] = Field(
        default="actual_content",
        description="Whether service was identified from actual website content or inferred"
    )


# -------------------------------------------------------------
# Section 5: Target Audience Identification
# -------------------------------------------------------------

class TargetAudienceSection(BaseModel):
    """Section 5: Target Audience Identification."""
    primary_audience: List[str] = Field(..., description="Primary decision-makers and buyer personas")
    secondary_audience: List[str] = Field(default_factory=list, description="Secondary influencers and stakeholders")
    industries: List[str] = Field(default_factory=list, description="Industry segments targeted")
    business_types: List[str] = Field(default_factory=list, description="Business types (e.g., B2B, B2C, Startups, SMBs, Enterprise)")
    customer_profiles: List[str] = Field(default_factory=list, description="Detailed customer profile personas")
    geographical_focus: Optional[str] = Field(default="Worldwide / Unspecified", description="Geographical focus if available")
    customer_needs: List[str] = Field(default_factory=list, description="Customer needs and core pain points")
    customer_interests: List[str] = Field(default_factory=list, description="Potential customer interests and affinities")
    recommended_segments_for_marketing: List[str] = Field(
        default_factory=list,
        description="Recommended audience segments for marketing campaigns"
    )


# -------------------------------------------------------------
# Top-Level Aggregated Models
# -------------------------------------------------------------

class BrandSummary(BaseModel):
    """High-level brand identity extracted from website."""
    name: str = Field(..., description="Brand or company name")
    category: str = Field(..., description="Main business category")
    summary: str = Field(..., description="Concise business summary")


class AnalysisPayload(BaseModel):
    """Container for the five core analysis sections."""
    competitor_analysis: CompetitorAnalysisSection
    target_search_queries: List[TargetSearchQuery] = Field(
        ...,
        min_length=5,
        max_length=5,
        description="Top 5 target search queries across platforms"
    )
    seo_improvements: SEOImprovementsSection
    top_services: List[ServiceItem] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Top services (up to 5)"
    )
    target_audience: TargetAudienceSection


class AnalysisMetadata(BaseModel):
    """Processing metadata including model and token estimates."""
    llm_provider: str = Field(..., description="LLM provider used")
    model_used: str = Field(..., description="Specific model utilized")
    processing_time_seconds: float = Field(..., description="Elapsed wall-clock processing time")
    cached: bool = Field(default=False, description="Whether result was served from cache")
    input_tokens_estimated: int = Field(default=0, description="Estimated prompt input tokens")
    output_tokens_estimated: int = Field(default=0, description="Estimated completion output tokens")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated API cost in USD")


class LinkAnalysisResponse(BaseModel):
    """Complete structured API response model."""
    success: bool = Field(default=True, description="Success status flag")
    website: str = Field(..., description="Analyzed website URL")
    brand: BrandSummary
    analysis: AnalysisPayload
    metadata: Optional[AnalysisMetadata] = None


class ErrorResponse(BaseModel):
    """Structured error response."""
    success: bool = Field(default=False, description="Failure status flag")
    error: str = Field(..., description="Error type or code")
    detail: str = Field(..., description="Human-readable explanation of error")
    website: Optional[str] = Field(default=None, description="URL that caused error if known")
