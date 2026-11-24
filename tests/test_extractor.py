"""Unit tests for website HTML extractor."""

import pytest
from app.services.website_extractor import WebsiteExtractor


SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dxora Technologies | Next-Gen AI Solutions</title>
    <meta name="description" content="Dxora provides enterprise AI consulting and cloud architecture.">
    <meta name="keywords" content="AI, Machine Learning, Cloud Architecture, FastAPI">
    <meta property="og:site_name" content="Dxora Technologies">
    <script type="application/ld+json">
    {"@context": "https://schema.org", "@type": "Organization", "name": "Dxora Technologies"}
    </script>
</head>
<body>
    <header>
        <nav>
            <a href="/services">Our Services</a>
            <a href="/solutions">Enterprise Solutions</a>
            <a href="/about">About Us</a>
            <a href="/pricing">Pricing</a>
        </nav>
    </header>
    <main>
        <h1>Empowering Enterprises with Autonomous AI</h1>
        <h2>Scalable Machine Learning Pipelines</h2>
        <p>Dxora builds custom LLM and AI workflows tailored for high-growth enterprises.</p>
        <h2>Cloud-Native Backend Architecture</h2>
        <p>Our microservices scale effortlessly across global cloud regions with 99.99% uptime.</p>
        <h3>Real-time Data Streaming</h3>
        <p>Process millions of events per second with distributed message queues.</p>
    </main>
    <footer>
        <p>&copy; 2026 Dxora Technologies. All rights reserved.</p>
    </footer>
</body>
</html>
"""


def test_html_parsing():
    extractor = WebsiteExtractor()
    data = extractor.parse_html(SAMPLE_HTML, target_url="https://dxora.com", final_url="https://dxora.com")

    assert data.title == "Dxora Technologies | Next-Gen AI Solutions"
    assert "enterprise AI consulting" in data.meta_description
    assert "AI" in data.meta_keywords
    assert data.og_site_name == "Dxora Technologies"
    assert data.inferred_brand_name == "Dxora Technologies"
    assert "Empowering Enterprises with Autonomous AI" in data.headings_h1
    assert "Scalable Machine Learning Pipelines" in data.headings_h2
    assert "Real-time Data Streaming" in data.headings_h3
    assert any("Services" in s for s in data.navigation_links)
    assert len(data.schema_org_data) == 1

    prompt_ctx = data.to_llm_prompt_context(max_length=5000)
    assert "Dxora Technologies" in prompt_ctx
    assert "Empowering Enterprises with Autonomous AI" in prompt_ctx
