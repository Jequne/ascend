from fastapi import APIRouter

from .admin_keys import router as admin_keys_router
from .auth import router as auth_router

router = APIRouter()
router.include_router(auth_router, tags=["auth"])
router.include_router(admin_keys_router, tags=["admin"])
