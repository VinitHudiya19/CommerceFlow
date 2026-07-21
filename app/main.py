import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import engine, Base, async_session
from app.common.initializer import seed_data
from app.common.exceptions import CommerceFlowException

# Import Routers
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.products.router import router as products_router
from app.cart.router import router as cart_router
from app.orders.router import router as orders_router
from app.payments.router import router as payments_router
from app.reviews.router import router as reviews_router
from app.inventory.router import router as inventory_router
from app.admin.router import router as admin_router
from app.wishlist.router import router as wishlist_router

# Lifespan manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create all tables in the database (dev convenience)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Run data seeder
    async with async_session() as session:
        await seed_data(session)
    
    yield

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(reviews_router)
app.include_router(inventory_router)
app.include_router(admin_router)
app.include_router(wishlist_router)

# -- Exception Handlers (RFC 7807 problem details mappings) --

@app.exception_handler(CommerceFlowException)
async def commerceflow_exception_handler(request: Request, exc: CommerceFlowException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_msg = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    return JSONResponse(
        status_code=400,
        content={"success": False, "message": f"Validation failed: {error_msg}"}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] Generic unhandled Exception occurred: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "An internal server error occurred"}
    )

# -- Static Files Frontend Serving --

@app.get("/")
async def serve_index():
    # Serve index.html on root path
    return FileResponse("static/index.html")

@app.get("/{path:path}")
async def serve_static(path: str):
    # Serves app.css, app.js and assets from static folder, fallback to index.html for SPA router
    file_path = f"static/{path}"
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse("static/index.html")
