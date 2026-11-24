"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
async def root():
    """Service status and quick links."""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
