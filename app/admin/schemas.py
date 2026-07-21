from decimal import Decimal
from pydantic import BaseModel

class DashboardStatsResponse(BaseModel):
    totalRevenue: Decimal
    totalUsers: int
    totalOrders: int
    pendingOrders: int
    lowStockProducts: int
