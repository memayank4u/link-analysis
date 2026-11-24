"""Integration tests for the FastAPI Link Analysis API."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app
from app.services.website_extractor import ExtractedWebsiteData


@pytest.fixture
def mock_extracted_data():
    """Fixture providing structured website extraction data for tests."""
    return ExtractedWebsiteData(
        url="https://dxora.com",
        final_url="https://dxora.com",
        domain="dxora.com",
        title="Dxora Technologies | Next-Gen AI & Cloud Solutions",
        meta_description="Dxora provides enterprise AI consulting and cloud architecture.",
        meta_keywords=["AI", "Machine Learning", "Cloud", "FastAPI"],
        og_site_name="Dxora Technologies",
        inferred_brand_name="Dxora Technologies",
        headings_h1=["Empowering Enterprises with Autonomous AI"],
        headings_h2=["Machine Learning", "Cloud Architecture", "Data Engineering"],
        headings_h3=["Enterprise Scalability"],
        navigation_links=["AI Consulting", "Cloud Architecture", "Data Engineering", "About Us"],
        key_paragraphs=["Dxora builds high-performance LLM solutions for global organizations."],
        cleaned_body_text="Dxora builds high-performance LLM solutions for global organizations."
    )


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test service discovery root endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["documentation"] == "/docs"


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_link_analysis_success(mock_extracted_data):
    """Test full analysis endpoint with mocked extractor to isolate intelligence pipeline."""
    transport = ASGITransport(app=app)

    with patch("app.services.analysis_service.WebsiteExtractor.fetch_and_extract", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_extracted_data

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/link-analysis",
                json={"url": "https://dxora.com"}
            )
            assert response.status_code == 200
            data = response.json()

            # Verify top-level structure
            assert data["success"] is True
            assert data["website"] == "https://dxora.com"
            assert "brand" in data
            assert data["brand"]["name"] == "Dxora Technologies"

            analysis = data["analysis"]
            
            # Section 1: Competitor vs Your Brand Details
            comp = analysis["competitor_analysis"]
            assert "brand_overview" in comp
            assert len(comp["competitors"]) >= 3
            assert len(comp["strengths"]) > 0
            assert len(comp["opportunities"]) > 0
            assert len(comp["comparison_table"]) > 0

            # Section 2: Top 5 Target Search Queries
            queries = analysis["target_search_queries"]
            assert len(queries) == 5
            for q in queries:
                assert "query" in q
                assert len(q["platforms"]) > 0
                assert "intent" in q
                assert "business_relevance" in q
                assert "target_audience" in q

            # Section 3: SEO Improvement
            seo = analysis["seo_improvements"]
            assert "primary_keyword" in seo
            assert len(seo["secondary_keywords"]) > 0
            assert "recommended_title" in seo
            assert "meta_description" in seo
            assert len(seo["supporting_content"]) > 0

            # Section 4: Top 5 Services
            services = analysis["top_services"]
            assert 1 <= len(services) <= 5
            for s in services:
                assert "service_name" in s
                assert "description" in s
                assert "target_industry" in s
                assert "target_customer" in s
                assert "main_benefit" in s
                assert s["source"] in ("actual_content", "inferred")

            # Section 5: Target Audience Identification
            audience = analysis["target_audience"]
            assert len(audience["primary_audience"]) > 0
            assert len(audience["industries"]) > 0
            assert len(audience["customer_needs"]) > 0
            assert len(audience["recommended_segments_for_marketing"]) > 0

            # Metadata verification
            assert "metadata" in data
            assert data["metadata"]["processing_time_seconds"] >= 0


@pytest.mark.asyncio
async def test_link_analysis_caching(mock_extracted_data):
    """Test that repeat requests to identical URL leverage caching."""
    transport = ASGITransport(app=app)

    with patch("app.services.analysis_service.WebsiteExtractor.fetch_and_extract", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_extracted_data

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp1 = await client.post("/link-analysis", json={"url": "https://dxora.com"})
            assert resp1.status_code == 200

            resp2 = await client.post("/link-analysis", json={"url": "https://dxora.com"})
            assert resp2.status_code == 200
            assert resp2.json()["metadata"]["cached"] is True


@pytest.mark.asyncio
async def test_ssrf_protection_in_api():
    """Verify that requests targeting private IPs/internal resources return 400 Bad Request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Loopback
        resp = await client.post("/link-analysis", json={"url": "http://127.0.0.1:4000/admin"})
        assert resp.status_code == 400
        assert resp.json()["error"] == "INVALID_URL_OR_SSRF"

        # Localhost
        resp2 = await client.post("/link-analysis", json={"url": "http://localhost:8080"})
        assert resp2.status_code == 400
        assert resp2.json()["error"] == "INVALID_URL_OR_SSRF"

        # AWS/GCP Metadata
        resp3 = await client.post("/link-analysis", json={"url": "http://169.254.169.254/latest/meta-data"})
        assert resp3.status_code == 400
        assert resp3.json()["error"] == "INVALID_URL_OR_SSRF"


@pytest.mark.asyncio
async def test_invalid_url_format():
    """Verify that malformed inputs trigger 400 Bad Request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/link-analysis", json={"url": "not-a-valid-domain-xyz"})
        assert resp.status_code == 400
        assert resp.json()["error"] == "INVALID_URL_OR_SSRF"
