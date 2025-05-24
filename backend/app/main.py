# backend/app/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

from app.core.content_generator import ContentGenerationService
from app.models.content import ContentGenerationRequest, ContentStatus
from app.models.responses import ContentGenerationResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store packages in memory for now (replace with database later)
content_packages = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    logger.info("🚀 Educational Content Generation System starting...")
    
    # Create audio directory
    Path("generated_audio").mkdir(exist_ok=True)
    
    # Initialize content service
    app.state.content_service = ContentGenerationService()
    logger.info("✅ Content generation service initialized")
    
    yield
    
    logger.info("📋 Shutting down...")


app = FastAPI(
    title="Educational Content Generation System",
    description="Generate coherent multi-modal educational content",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve audio files
if os.path.exists("generated_audio"):
    app.mount("/audio", StaticFiles(directory="generated_audio"), name="audio")


@app.get("/")
async def root():
    return {
        "service": "Educational Content Generation System",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/api/v1/content/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate educational content package"""
    try:
        logger.info(f"Starting generation for {request.subject}/{request.skill}")
        
        # Generate package ID
        package_id = f"pkg_{int(__import__('time').time())}"
        
        # Store initial status
        content_packages[package_id] = {
            "status": "generating",
            "request": request.dict(),
            "created_at": __import__('datetime').datetime.now().isoformat()
        }
        
        # Start generation in background
        background_tasks.add_task(generate_content_async, package_id, request)
        
        return ContentGenerationResponse(
            package_id=package_id,
            status="generating",
            message="Content generation started",
            estimated_completion_time=__import__('datetime').datetime.now().isoformat(),
            stages=["master_context", "reading", "visual", "audio", "practice"]
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_content_async(package_id: str, request: ContentGenerationRequest):
    """Background task for content generation"""
    try:
        # Get content service
        content_service = ContentGenerationService()
        
        # Generate package
        package = await content_service.generate_content_package(request)
        
        # Store completed package
        content_packages[package_id] = {
            "status": "completed",
            "package": package.dict(),
            "created_at": package.created_at.isoformat()
        }
        
        logger.info(f"Generation completed for package {package_id}")
        
    except Exception as e:
        logger.error(f"Background generation failed: {str(e)}")
        content_packages[package_id] = {
            "status": "failed",
            "error": str(e),
            "created_at": __import__('datetime').datetime.now().isoformat()
        }


@app.get("/api/v1/content/status/{package_id}")
async def get_generation_status(package_id: str):
    """Get generation status"""
    if package_id not in content_packages:
        raise HTTPException(status_code=404, detail="Package not found")
    
    return content_packages[package_id]


@app.get("/api/v1/content/package/{package_id}")
async def get_content_package(package_id: str):
    """Get completed content package"""
    if package_id not in content_packages:
        raise HTTPException(status_code=404, detail="Package not found")
    
    package_data = content_packages[package_id]
    
    if package_data["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Package status: {package_data['status']}")
    
    return package_data["package"]


@app.get("/api/v1/content/packages")
async def list_packages():
    """List all content packages"""
    return {
        "packages": [
            {
                "package_id": pid,
                "status": data["status"],
                "created_at": data["created_at"],
                **({"subject": data["request"]["subject"], 
                   "skill": data["request"]["skill"]} if "request" in data else {})
            }
            for pid, data in content_packages.items()
        ],
        "total": len(content_packages)
    }


@app.post("/api/v1/review/approve/{package_id}")
async def approve_package(package_id: str):
    """Approve a content package"""
    if package_id not in content_packages:
        raise HTTPException(status_code=404, detail="Package not found")
    
    package_data = content_packages[package_id]
    if "package" in package_data:
        package_data["package"]["review_status"] = "approved"
    
    return {"status": "approved", "package_id": package_id}


@app.post("/api/v1/review/reject/{package_id}")
async def reject_package(package_id: str, feedback: str):
    """Reject a content package"""
    if package_id not in content_packages:
        raise HTTPException(status_code=404, detail="Package not found")
    
    package_data = content_packages[package_id]
    if "package" in package_data:
        package_data["package"]["review_status"] = "needs_revision"
        package_data["package"]["review_notes"] = [feedback]
    
    return {"status": "rejected", "package_id": package_id, "feedback": feedback}


@app.get("/api/v1/review/pending")
async def get_pending_reviews():
    """Get packages needing review"""
    pending = [
        {
            "package_id": pid,
            "package": data.get("package", {}),
            "created_at": data["created_at"]
        }
        for pid, data in content_packages.items()
        if data["status"] == "completed" and 
           data.get("package", {}).get("review_status", "pending") == "pending"
    ]
    
    return {"pending_packages": pending, "count": len(pending)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)