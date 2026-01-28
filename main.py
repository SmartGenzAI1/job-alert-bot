from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update
import logging
import time
import os
from typing import Dict, Any

from config import WEBHOOK_BASE_URL, WEBHOOK_TOKEN, logger
from bot import create_bot
from database.db import init_db, get_db_stats, close_db

app = FastAPI(
    title="Job Alert Bot API",
    description="Production-ready Telegram bot for job alerts",
    version="1.0.0"
)

# Add CORS middleware for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize bot and database
tg_app = None
startup_time = time.time()


@app.on_event("startup")
async def startup():
    """Initialize the application on startup."""
    global tg_app
    
    try:
        logger.info("Starting Job Alert Bot...")
        
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Initialize bot
        tg_app = create_bot()
        await tg_app.initialize()
        logger.info("Telegram bot initialized successfully")
        
        # Set webhook
        webhook_url = f"{WEBHOOK_BASE_URL}/webhook/{WEBHOOK_TOKEN}"
        await tg_app.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
        
        logger.info("Job Alert Bot startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Clean up resources on shutdown."""
    try:
        if tg_app:
            await tg_app.shutdown()
            logger.info("Telegram bot shutdown completed")
        
        close_db()
        logger.info("Database connection closed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    """Handle incoming webhook requests from Telegram."""
    try:
        # Validate webhook token
        if token != WEBHOOK_TOKEN:
            logger.warning(f"Invalid webhook token: {token}")
            return PlainTextResponse("Forbidden", 403)

        # Parse request data
        data = await request.json()
        
        # Process update
        if tg_app:
            update = Update.de_json(data, tg_app.bot)
            await tg_app.process_update(update)
        
        return PlainTextResponse("ok", 200)
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return PlainTextResponse("Internal Server Error", 500)


@app.get("/")
async def health():
    """Health check endpoint."""
    try:
        uptime = time.time() - startup_time
        
        # Get database stats
        db_stats = get_db_stats()
        
        health_status = {
            "status": "healthy",
            "uptime_seconds": round(uptime, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "database": {
                "status": "connected" if db_stats else "error",
                "total_users": db_stats.get("total_users", 0) if db_stats else 0,
                "total_jobs": db_stats.get("total_jobs", 0) if db_stats else 0,
            },
            "webhook": {
                "base_url": WEBHOOK_BASE_URL,
                "configured": bool(WEBHOOK_TOKEN)
            }
        }
        
        return JSONResponse(content=health_status, status_code=200)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            },
            status_code=500
        )


@app.get("/api/stats")
async def get_stats():
    """Get application statistics."""
    try:
        if not tg_app:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        db_stats = get_db_stats()
        
        stats = {
            "bot": {
                "token_configured": bool(WEBHOOK_TOKEN),
                "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/{WEBHOOK_TOKEN}"
            },
            "database": db_stats,
            "system": {
                "uptime_seconds": round(time.time() - startup_time, 2),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            }
        }
        
        return JSONResponse(content=stats, status_code=200)
        
    except Exception as e:
        logger.error(f"Stats endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health/detailed")
async def detailed_health():
    """Detailed health check with all system components."""
    try:
        checks = {}
        
        # Database check
        try:
            db_stats = get_db_stats()
            checks["database"] = {
                "status": "healthy" if db_stats else "error",
                "details": db_stats or {"error": "Unable to retrieve stats"}
            }
        except Exception as e:
            checks["database"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
        
        # Bot check
        try:
            if tg_app and hasattr(tg_app, 'bot') and tg_app.bot:
                bot_info = await tg_app.bot.get_me()
                checks["bot"] = {
                    "status": "healthy",
                    "details": {
                        "username": bot_info.username,
                        "first_name": bot_info.first_name,
                        "id": bot_info.id
                    }
                }
            else:
                checks["bot"] = {
                    "status": "error",
                    "details": {"error": "Bot not initialized"}
                }
        except Exception as e:
            checks["bot"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
        
        # Webhook check
        try:
            if tg_app and hasattr(tg_app, 'bot') and tg_app.bot:
                webhook_info = await tg_app.bot.get_webhook_info()
                checks["webhook"] = {
                    "status": "healthy" if webhook_info.url else "error",
                    "details": {
                        "url": webhook_info.url,
                        "has_custom_certificate": webhook_info.has_custom_certificate,
                        "pending_update_count": webhook_info.pending_update_count
                    }
                }
            else:
                checks["webhook"] = {
                    "status": "error",
                    "details": {"error": "Bot not initialized"}
                }
        except Exception as e:
            checks["webhook"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
        
        # Overall status
        all_healthy = all(check["status"] == "healthy" for check in checks.values())
        
        return JSONResponse(
            content={
                "status": "healthy" if all_healthy else "degraded",
                "checks": checks,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            },
            status_code=200 if all_healthy else 503
        )
        
    except Exception as e:
        logger.error(f"Detailed health check error: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            },
            status_code=500
        )


# Add 404 handler
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        content={"error": "Endpoint not found", "path": str(request.url)},
        status_code=404
    )


# Add 500 handler
@app.exception_handler(500)
async def server_error_handler(request, exc):
    logger.error(f"Server error: {exc}")
    return JSONResponse(
        content={"error": "Internal server error", "path": str(request.url)},
        status_code=500
    )
