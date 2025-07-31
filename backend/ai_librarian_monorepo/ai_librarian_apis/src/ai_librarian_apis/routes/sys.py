from fastapi import APIRouter
from schemas import HealthResponse

sys_router = APIRouter(prefix="/sys", tags=["sys"])


@sys_router.get("/health", summary="Health Check")
def health() -> HealthResponse:
    """Provides a simple health check endpoint to verify that the API service
    is running and responsive.
    """
    return HealthResponse(status="ok")


# TODO: add a route to get the logs
