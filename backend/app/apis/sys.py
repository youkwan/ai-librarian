from fastapi import APIRouter

from app.models.schema import HealthResponse

router = APIRouter(prefix="/sys", tags=["sys"])


@router.get(
    "/health",
    summary="Health Check",
    description="Check the health of the API",
    response_model=HealthResponse,
)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
