from fastapi import APIRouter

from app.models.schemas import HealthResponse

sys_router = APIRouter(prefix="/sys", tags=["sys"])


@sys_router.get(
    "/health",
    summary="Health Check",
    description="Check the health of the API",
    response_model=HealthResponse,
)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


# TODO: add a route to get the logs
