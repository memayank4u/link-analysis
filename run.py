"""Application entrypoint runner script."""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"============================================================")
    print(f" Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f" Local URL:      http://{settings.HOST}:{settings.PORT}")
    print(f" API Docs:       http://localhost:{settings.PORT}/docs")
    print(f" Health Check:   http://localhost:{settings.PORT}/health")
    print(f" Active LLM:     {settings.LLM_PROVIDER}")
    print(f"============================================================")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
