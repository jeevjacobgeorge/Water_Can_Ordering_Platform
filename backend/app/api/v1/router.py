"""
API v1 router — aggregates all v1 endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.customers import router as customers_router
from app.api.v1.orders import refill_router, router as orders_router
from app.api.v1.payments import router as payments_router
from app.api.v1.staff import router as staff_router
from app.api.v1.businesses import router as businesses_router
from app.api.v1.platform import router as platform_router
from app.api.v1.products import router as products_router

router = APIRouter(prefix="/api/v1")


# Health check at API level
@router.get("/health", tags=["health"])
async def api_health():
    return {"status": "ok", "version": "v1"}


router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(customers_router)
router.include_router(orders_router)
router.include_router(refill_router)
router.include_router(products_router)
router.include_router(payments_router)
router.include_router(staff_router)
router.include_router(businesses_router)
router.include_router(platform_router)
