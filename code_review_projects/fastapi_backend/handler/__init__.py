from fastapi import APIRouter

from fastapi_backend.handler.campaign import router as campaign_router
from fastapi_backend.handler.healthcheck import healthcheck_router

router = APIRouter()
router.include_router(healthcheck_router, prefix="/api/healthcheck")
router.include_router(campaign_router, prefix="/api/campaigns", tags=["Campaign"])