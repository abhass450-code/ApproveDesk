from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import ai, alerts, applications, auth, compliance, queries, users
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.2.0", description="Prototype API for the ApproveDesk SIH26262 project")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(applications.router, prefix=settings.api_prefix)
app.include_router(queries.router, prefix=settings.api_prefix)
app.include_router(compliance.router, prefix=settings.api_prefix)
app.include_router(alerts.router, prefix=settings.api_prefix)
app.include_router(ai.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)


@app.get(f"{settings.api_prefix}/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
