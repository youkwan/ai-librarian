from ai_librarian_apis.schemas.error import ErrorResponse
from ai_librarian_apis.schemas.system import HealthResponse
from fastapi import APIRouter

system_router = APIRouter(prefix="/system", tags=["System"])


@system_router.get("/health", summary="Health Check", responses={500: {"model": ErrorResponse}})
def check_health() -> HealthResponse:
    """A simple health check endpoint to verify that the API service
    is running and responsive.
    """
    return HealthResponse(status="ok")
