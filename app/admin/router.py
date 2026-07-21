from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.schemas import ApiResponse
from app.admin.schemas import DashboardStatsResponse
from app.security.dependencies import get_admin_user
from app.admin.service import get_dashboard_stats

router = APIRouter(prefix="/api/admin", tags=["Admin Statistics"])

@router.get("/dashboard", response_model=ApiResponse[DashboardStatsResponse])
async def get_dashboard(
    _admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve administrative dashboard summary (Admin only)
    data = await get_dashboard_stats(db)
    return ApiResponse(success=True, message="Admin dashboard statistics retrieved", data=data)
