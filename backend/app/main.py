# backend/app/main.py - FastAPI Application with Storage Integration
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from typing import List, Optional
import logging
import asyncio
from contextlib import asynccontextmanager

from datetime import datetime, timezone

# Import configuration first - this handles environment loading automatically
from app.config import settings

from app.core.content_generator import ContentGenerationService
from app.models.content import ContentGenerationRequest, ContentPackage
from app.database.cosmos_client import cosmos_service
from app.database.blob_storage import blob_storage_service

# Configure logging based on settings
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Educational Content Generation API...")
    
    # Initialize storage services
    logger.info("📡 Initializing storage services...")
    
    cosmos_init = await cosmos_service.initialize()
    blob_init = await blob_storage_service.initialize()
    
    if not cosmos_init:
        logger.error("❌ Failed to initialize Cosmos DB")
        raise RuntimeError("Cosmos DB initialization failed")
    
    if not blob_init:
        logger.error("❌ Failed to initialize Blob Storage")
        raise RuntimeError("Blob Storage initialization failed")
    
    logger.info("✅ All storage services initialized successfully")
    logger.info("🎉 API is ready to serve requests!")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down API...")
    cosmos_service.close()
    blob_storage_service.close()
    logger.info("✅ Shutdown complete")


# Create FastAPI app with configuration
app = FastAPI(
    title=settings.APP_NAME,
    description="Generate comprehensive educational content packages using Gemini AI with cloud storage",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Add CORS middleware with configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize content service - MOVED INSIDE ENDPOINT TO AVOID MODULE-LEVEL INITIALIZATION
# content_service = ContentGenerationService()  # <-- REMOVE THIS LINE


def get_content_service():
    """Dependency to get content service instance"""
    return ContentGenerationService()


@app.get("/")
async def root():
    """Root endpoint with configuration info"""
    return {
        "message": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
        "features": {
            "blob_storage": settings.blob_storage_enabled,
            "development_mode": settings.is_development
        }
    }


@app.post(f"{settings.API_V1_PREFIX}/generate-content", response_model=ContentPackage)
async def generate_content(
    request: ContentGenerationRequest, 
    background_tasks: BackgroundTasks,
    content_service: ContentGenerationService = Depends(get_content_service)
):
    """Generate a new educational content package with all components"""
    try:
        logger.info(f"🎯 Content generation request: {request.subject}/{request.unit}/{request.skill}")
        
        # Generate content package (this will automatically store in cloud)
        package = await content_service.generate_content_package(request)
        
        logger.info(f"✅ Content package generated successfully: {package.id}")
        
        # Add background task for any cleanup if needed
        background_tasks.add_task(log_generation_complete, package.id, package.generation_metadata.generation_time_ms)
        
        return package
        
    except Exception as e:
        logger.error(f"❌ Content generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Content generation failed: {str(e)}"
        )


@app.get(f"{settings.API_V1_PREFIX}/content/{{package_id}}", response_model=ContentPackage)
async def get_content_package(
    package_id: str, 
    subject: str, 
    unit: str,
    content_service: ContentGenerationService = Depends(get_content_service)
):
    """Get a specific content package by ID"""
    try:
        logger.info(f"📖 Retrieving package: {package_id}")
        
        package = await content_service.get_content_package(package_id, subject, unit)
        
        logger.info(f"✅ Package retrieved: {package_id}")
        return package
        
    except ValueError as e:
        logger.warning(f"⚠️ Package not found: {package_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to retrieve package {package_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content package")


@app.get(f"{settings.API_V1_PREFIX}/content", response_model=List[ContentPackage])
async def list_content_packages(
    subject: Optional[str] = None,
    unit: Optional[str] = None,
    limit: int = 100,
    status: Optional[str] = None
):
    """List content packages with optional filtering"""
    try:
        logger.info(f"📋 Listing packages - Subject: {subject}, Unit: {unit}, Limit: {limit}")
        
        packages = await cosmos_service.list_content_packages(
            subject=subject,
            unit=unit,
            status=status,
            limit=limit
        )
        
        logger.info(f"✅ Retrieved {len(packages)} packages")
        return packages
        
    except Exception as e:
        logger.error(f"❌ Failed to list packages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list content packages")


@app.delete(f"{settings.API_V1_PREFIX}/content/{{package_id}}")
async def delete_content_package(
    package_id: str, 
    subject: str, 
    unit: str,
    content_service: ContentGenerationService = Depends(get_content_service)
):
    """Delete a content package and all associated files"""
    try:
        logger.info(f"🗑️ Deleting package: {package_id}")
        
        deleted = await content_service.delete_content_package(package_id, subject, unit)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Content package not found")
        
        logger.info(f"✅ Package deleted: {package_id}")
        return {"message": f"Content package {package_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete package {package_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete content package")


@app.get(f"{settings.API_V1_PREFIX}/audio/{{package_id}}/{{filename}}")
async def get_audio_file(package_id: str, filename: str):
    """Get audio file URL (redirect to Azure Blob Storage)"""
    try:
        logger.info(f"🎵 Audio request: {package_id}/{filename}")
        
        audio_url = await blob_storage_service.get_audio_file_url(package_id, filename)
        
        if not audio_url:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        logger.info(f"✅ Audio URL generated: {package_id}/{filename}")
        
        # Redirect to the blob storage URL
        return RedirectResponse(url=audio_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get audio URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get audio file")


@app.get(f"{settings.API_V1_PREFIX}/packages/{{subject}}")
async def get_packages_by_subject(subject: str, unit: Optional[str] = None):
    """Get all packages for a specific subject, optionally filtered by unit"""
    try:
        if unit:
            packages = await cosmos_service.get_packages_by_subject_unit(subject, unit)
        else:
            packages = await cosmos_service.list_content_packages(subject=subject)
        
        return {
            "subject": subject,
            "unit": unit,
            "total_packages": len(packages),
            "packages": packages
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get packages for {subject}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get packages for {subject}")

@app.get(f"{settings.API_V1_PREFIX}/packages/review-queue", response_model=List[ContentPackage])
async def get_packages_for_review(
    limit: int = 50,
    subject: Optional[str] = None,
    unit: Optional[str] = None
):
    """Get packages that need review (status = 'generated')"""
    try:
        logger.info(f"📋 Getting packages for review - Subject: {subject}, Unit: {unit}")
        
        packages = await cosmos_service.list_content_packages(
            subject=subject,
            unit=unit,
            status="generated",  # Only get packages that need review
            limit=limit
        )
        
        logger.info(f"✅ Retrieved {len(packages)} packages for review")
        return packages
        
    except Exception as e:
        logger.error(f"❌ Failed to get review queue: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get packages for review")

@app.put(f"{settings.API_V1_PREFIX}/packages/{{package_id}}/status")
async def update_package_status(
    package_id: str,
    subject: str,
    unit: str,
    status_update: dict
):
    """Update the status of a content package (approve, reject, etc.)"""
    try:
        new_status = status_update.get("status")
        reviewer_notes = status_update.get("notes", "")
        reviewer_id = status_update.get("reviewer_id")
        
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        # Valid status transitions
        valid_statuses = ["approved", "rejected", "needs_revision", "under_review"]
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        logger.info(f"📝 Updating package {package_id} status to: {new_status}")
        
        partition_key = f"{subject}-{unit}"
        
        # Get the current package
        package = await cosmos_service.get_content_package(package_id, partition_key)
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Update the package - convert to dict properly
        package_dict = package.model_dump()
        old_status = package_dict.get("status", "generated")
        
        # Update fields
        package_dict["status"] = new_status
        package_dict["review_status"] = new_status
        package_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Add review information if provided
        if reviewer_id:
            package_dict["reviewed_by"] = reviewer_id
            package_dict["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Add notes if provided
        if reviewer_notes:
            if "review_notes" not in package_dict:
                package_dict["review_notes"] = []
            
            package_dict["review_notes"].append({
                "note": reviewer_notes,
                "status": new_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reviewer_id": reviewer_id
            })
        
        # Update in database using the dict directly
        try:
            updated_package = ContentPackage(**package_dict)
            result = await cosmos_service.update_content_package(updated_package)
            
            logger.info(f"✅ Package {package_id} status updated to: {new_status}")
            
            return {
                "message": f"Package status updated to {new_status}",
                "package_id": package_id,
                "old_status": old_status,
                "new_status": new_status,
                "updated_at": package_dict["updated_at"],
                "package": result.model_dump()  # Convert to dict for JSON response
            }
            
        except Exception as update_error:
            logger.error(f"❌ Database update failed: {str(update_error)}")
            raise HTTPException(status_code=500, detail=f"Database update failed: {str(update_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update package status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update package status: {str(e)}")


@app.get(f"{settings.API_V1_PREFIX}/packages/{{package_id}}/review-info")
async def get_package_review_info(package_id: str, subject: str, unit: str):
    """Get review information for a specific package"""
    try:
        partition_key = f"{subject}-{unit}"
        package = await cosmos_service.get_content_package(package_id, partition_key)
        
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Convert to dict first to safely access fields
        package_dict = package.model_dump()
        
        # Extract review-related information safely
        review_info = {
            "package_id": package_id,
            "current_status": package_dict.get("status", "generated"),
            "review_status": package_dict.get("review_status", "pending"),
            "reviewed_by": package_dict.get("reviewed_by"),
            "reviewed_at": package_dict.get("reviewed_at"),
            "review_notes": package_dict.get("review_notes", []),
            "created_at": package_dict.get("created_at"),
            "updated_at": package_dict.get("updated_at"),
            "subject": package_dict.get("subject"),
            "unit": package_dict.get("unit"),
            "skill": package_dict.get("skill"),
            "subskill": package_dict.get("subskill")
        }
        
        return review_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get review info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get package review info: {str(e)}")

@app.get(f"{settings.API_V1_PREFIX}/health")
async def health_check():
    """Comprehensive health check for all services"""
    try:
        logger.info("🏥 Running health check...")
        
        # Check storage services
        cosmos_health = await cosmos_service.health_check()
        blob_health = await blob_storage_service.health_check()
        
        # Determine overall health
        cosmos_healthy = cosmos_health.get("status") == "healthy"
        blob_healthy = blob_health.get("status") == "healthy"
        overall_healthy = cosmos_healthy and blob_healthy
        
        health_status = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": cosmos_health.get("timestamp"),
            "services": {
                "cosmos_db": {
                    "status": cosmos_health.get("status"),
                    "total_documents": cosmos_health.get("total_documents"),
                    "database": cosmos_health.get("database"),
                    "container": cosmos_health.get("container")
                },
                "blob_storage": {
                    "status": blob_health.get("status"),
                    "container": blob_health.get("container", "unknown"),
                    "recent_blobs": blob_health.get("total_recent_blobs")
                },
                "content_generation": {
                    "status": "ready",
                    "service": "ContentGenerationService"
                }
            }
        }
        
        # Return appropriate status code
        status_code = 200 if overall_healthy else 503
        
        logger.info(f"✅ Health check complete - Status: {health_status['status']}")
        
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "services": {"error": "Health check failed"}
            },
            status_code=503
        )


@app.get(f"{settings.API_V1_PREFIX}/storage/stats")
async def get_storage_stats():
    """Get storage usage statistics"""
    try:
        blob_stats = await blob_storage_service.get_storage_stats()
        
        # Get package count from Cosmos DB
        packages = await cosmos_service.list_content_packages(limit=1000)
        
        return {
            "blob_storage": blob_stats,
            "cosmos_db": {
                "total_packages": len(packages),
                "database": cosmos_service.database.id if cosmos_service.database else "unknown",
                "container": cosmos_service.container.id if cosmos_service.container else "unknown"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get storage stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get storage statistics")


# Background task functions
async def log_generation_complete(package_id: str, generation_time_ms: int):
    """Background task to log generation completion"""
    logger.info(f"📊 Package {package_id} generation completed in {generation_time_ms}ms")


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid input", "detail": str(exc)}
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )