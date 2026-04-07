from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.logging import configure_logging
from app.middleware.auth_middleware import AuthMiddleware


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title="JobSpark Python Backend", version="0.1.0")

    # Keep permissive CORS in scaffold; tighten in later steps.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Scaffold middleware: parse JWT and store user_id in request.state
    app.add_middleware(AuthMiddleware)

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


app = create_app()

