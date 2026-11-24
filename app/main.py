"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

from app.config import settings
from app.schemas import ErrorResponse, LinkAnalysisRequest, LinkAnalysisResponse
from app.services.analysis_service import AnalysisService
from app.services.website_extractor import WebsiteExtractionError
from app.utils.validators import URLValidationError

# Configure structured logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dxora.link_analysis")

# Shared analysis service instance
analysis_service = AnalysisService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for FastAPI application."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Active LLM provider configured: {settings.LLM_PROVIDER}")
    yield
    logger.info("Shutting down link analysis service.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-ready FastAPI service that extracts, analyzes, and interprets website URLs using LLMs. "
        "Delivers structured insights across 5 core dimensions: Competitor Analysis, Target Search Queries, "
        "SEO Improvements, Top 5 Services, and Target Audience Identification."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Enable CORS for cross-origin frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(URLValidationError)
async def url_validation_exception_handler(request: Request, exc: URLValidationError):
    """Handle invalid URL and SSRF attempts."""
    logger.warning(f"URL validation failed: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            success=False,
            error="INVALID_URL_OR_SSRF",
            detail=str(exc)
        ).model_dump()
    )


@app.exception_handler(WebsiteExtractionError)
async def website_extraction_exception_handler(request: Request, exc: WebsiteExtractionError):
    """Handle inaccessible or failing external websites."""
    logger.warning(f"Website extraction error: {str(exc)}")
    http_status = exc.status_code if exc.status_code and exc.status_code >= 400 else status.HTTP_502_BAD_GATEWAY
    return JSONResponse(
        status_code=http_status,
        content=ErrorResponse(
            success=False,
            error="WEBSITE_EXTRACTION_FAILED",
            detail=str(exc)
        ).model_dump()
    )


@app.get("/", tags=["General"])
async def root(request: Request):
    """Service status and quick links."""
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        return HTMLResponse(content=HTML_TESTER, status_code=200)

    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "documentation": "/docs",
        "endpoint": "POST /link-analysis",
        "configured_provider": settings.LLM_PROVIDER,
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Liveness probe for monitoring and deployments."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "provider": settings.LLM_PROVIDER,
    }


@app.post(
    "/link-analysis",
    response_model=LinkAnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
    summary="Analyze website URL and generate structured intelligence",
    responses={
        200: {
            "description": "Structured 5-section website analysis generated successfully",
            "model": LinkAnalysisResponse,
        },
        400: {
            "description": "Invalid URL format or SSRF restriction triggered",
            "model": ErrorResponse,
        },
        502: {
            "description": "Target website was unreachable, blocked, or returned server error",
            "model": ErrorResponse,
        },
        504: {
            "description": "Target website request timed out",
            "model": ErrorResponse,
        },
    },
)
async def analyze_link(payload: LinkAnalysisRequest) -> LinkAnalysisResponse:
    """
    Analyze a given website URL using LLM intelligence.
    
    Generates 5 structured sections:
    - **Section 1**: Competitor vs Your Brand Details
    - **Section 2**: Top 5 Target Search Queries (Google, Facebook, Instagram, LinkedIn, X)
    - **Section 3**: SEO Improvements (Keywords, SEO Title, Meta Description, Supporting Content)
    - **Section 4**: Top 5 Services (Name, Description, Target Industry, Customer, Benefit, Source)
    - **Section 5**: Target Audience Identification (Personas, Industries, Needs, Marketing Segments)
    """
    logger.info(f"Incoming link-analysis request for URL: {payload.url}")
    try:
        response = await analysis_service.analyze_url(payload.url)
        return response
    except (URLValidationError, WebsiteExtractionError):
        raise
    except Exception as exc:
        logger.error(f"Unexpected error processing analysis for {payload.url}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during website analysis: {str(exc)}"
        )


HTML_TESTER = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Link Analysis API | Live Interactive Tester</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', -apple-system, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; line-height: 1.5; }
        .container { max-width: 900px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 32px; padding: 24px 0; border-bottom: 1px solid #1e293b; }
        .badge { display: inline-block; background: #0284c7; color: white; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; text-transform: uppercase; margin-bottom: 12px; }
        h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; color: #ffffff; }
        p.subtitle { color: #94a3b8; font-size: 15px; }
        .links-bar { display: flex; gap: 12px; justify-content: center; margin-top: 16px; }
        .links-bar a { color: #38bdf8; text-decoration: none; font-size: 13px; font-weight: 500; background: #1e293b; padding: 6px 14px; border-radius: 6px; border: 1px solid #334155; }
        .links-bar a:hover { background: #334155; }
        .card { background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3); margin-bottom: 24px; }
        .input-group { display: flex; gap: 12px; }
        input[type="url"] { flex: 1; padding: 14px 18px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #ffffff; font-size: 15px; outline: none; }
        input[type="url"]:focus { border-color: #38bdf8; box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2); }
        button { padding: 14px 28px; border-radius: 8px; border: none; background: #0284c7; color: white; font-weight: 600; font-size: 15px; cursor: pointer; transition: background 0.15s; white-space: nowrap; }
        button:hover { background: #0369a1; }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .notice { font-size: 12px; color: #94a3b8; margin-top: 8px; }
        #output { margin-top: 24px; display: none; }
        pre { background: #020617; padding: 20px; border-radius: 8px; overflow-x: auto; color: #a5f3fc; font-size: 13px; border: 1px solid #1e293b; max-height: 600px; }
        .spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid #ffffff; border-radius: 50%; border-top-color: transparent; animation: spin 0.8s linear infinite; margin-right: 8px; vertical-align: middle; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">Dxora Technologies Practical Test</span>
            <h1>AI-Powered Website Link Analysis API</h1>
            <p class="subtitle">Extracts, comprehends, and generates structured 5-section strategic intelligence for any website URL.</p>
            <div class="links-bar">
                <a href="/docs" target="_blank">Interactive Swagger Docs (/docs)</a>
                <a href="/health" target="_blank">Health Check (/health)</a>
                <a href="https://github.com/memayank4u/link-analysis" target="_blank">GitHub Repository</a>
            </div>
        </div>

        <div class="card">
            <h2 style="font-size: 18px; margin-bottom: 12px;">Test Any Website URL</h2>
            <div class="input-group">
                <input type="url" id="targetUrl" value="https://example.com" placeholder="https://example.com" required>
                <button id="submitBtn" onclick="analyzeUrl()">Analyze Website</button>
            </div>
            <p class="notice">Note: The underlying REST endpoint is <code>POST /link-analysis</code> with JSON body <code>{"url": "..."}</code>.</p>
        </div>

        <div id="output" class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 style="font-size: 16px;">Structured Response (JSON)</h3>
                <span id="timingBadge" style="font-size: 12px; color: #38bdf8;"></span>
            </div>
            <pre><code id="jsonResult"></code></pre>
        </div>
    </div>

    <script>
        async function analyzeUrl() {
            const urlInput = document.getElementById('targetUrl');
            const submitBtn = document.getElementById('submitBtn');
            const outputDiv = document.getElementById('output');
            const jsonResult = document.getElementById('jsonResult');
            const timingBadge = document.getElementById('timingBadge');

            const url = urlInput.value.trim();
            if (!url) return alert('Please enter a valid website URL');

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span> Analyzing...';
            outputDiv.style.display = 'block';
            jsonResult.textContent = 'Fetching and analyzing website content...';
            timingBadge.textContent = '';

            const startTime = performance.now();
            try {
                const response = await fetch('/link-analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();
                const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
                timingBadge.textContent = `Completed in ${elapsed}s (HTTP ${response.status})`;
                jsonResult.textContent = JSON.stringify(data, null, 2);
            } catch (err) {
                jsonResult.textContent = 'Error: ' + err.message;
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Analyze Website';
            }
        }
    </script>
</body>
</html>
"""


@app.get("/link-analysis", include_in_schema=False)
async def link_analysis_browser_view(request: Request):
    """
    Handle direct browser clicks to /link-analysis.
    Returns an interactive HTML UI for browser visits, or guidance JSON for API clients.
    """
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        return HTMLResponse(content=HTML_TESTER, status_code=200)

    return {
        "message": "The /link-analysis endpoint requires an HTTP POST request.",
        "expected_method": "POST",
        "expected_payload": {"url": "https://example.com"},
        "interactive_docs": "/docs",
        "sample_curl": f'curl -X POST "{request.base_url}link-analysis" -H "Content-Type: application/json" -d \'{"url": "https://example.com"}\''
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
