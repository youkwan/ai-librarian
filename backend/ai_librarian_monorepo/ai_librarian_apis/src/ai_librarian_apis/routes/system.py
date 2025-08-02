from ai_librarian_apis.schemas.system import HealthResponse
from fastapi import APIRouter

system_router = APIRouter(prefix="/system", tags=["system"])


@system_router.get("/health", summary="Health Check")
def check_health() -> HealthResponse:
    """A simple health check endpoint to verify that the API service
    is running and responsive.
    """
    return HealthResponse(status="ok")
