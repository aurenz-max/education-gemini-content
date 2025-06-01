# backend/app/main.py - FastAPI Application with Storage Integration
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from typing import List, Optional, Dict, Any, Union
import logging
import asyncio
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
import json

from datetime import datetime, timezone

# Import configuration first - this handles environment loading automatically
from app.config import settings

from app.core.content_generator import ContentGenerationService
from app.models.content import ContentGenerationRequest, ContentPackage, RevisionRequest
from app.database.cosmos_client import cosmos_service
from app.database.blob_storage import blob_storage_service

# Import the curriculum service and models
from app.core.curriculum_service import CurriculumService
from app.models.curriculum import (
    CurriculumReferenceRequest, 
    ManualContentRequest, 
    EnhancedContentGenerationRequest
)

# Configure logging based on settings
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FIXED: Create a singleton instance of CurriculumService
# This ensures the same instance is used across all requests
curriculum_service_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    global curriculum_service_instance
    
    # Startup
    logger.info("🚀 Starting Educational Content Generation API...")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")
    logger.info(f"   TTS Enabled: {settings.tts_enabled}")
    logger.info(f"   Blob Storage: {settings.blob_storage_enabled}")
    
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
    
    # FIXED: Initialize the curriculum service singleton
    logger.info("📚 Initializing curriculum service...")
    curriculum_service_instance = CurriculumService()
    
    logger.info("✅ All storage services initialized successfully")
    logger.info("🎉 API is ready to serve requests!")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down API...")
    cosmos_service.close()
    blob_storage_service.close()
    curriculum_service_instance = None
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

# IMPROVED: Service dependencies with proper initialization
def get_content_service():
    """Dependency to get content service instance with proper initialization"""
    try:
        return ContentGenerationService()
    except Exception as e:
        logger.error(f"❌ Failed to initialize ContentGenerationService: {e}")
        raise HTTPException(
            status_code=503, 
            detail="Content generation service unavailable"
        )

def get_curriculum_service():
    """FIXED: Dependency to get the singleton curriculum service instance"""
    global curriculum_service_instance
    if curriculum_service_instance is None:
        logger.error("❌ Curriculum service not initialized")
        raise HTTPException(
            status_code=503, 
            detail="Curriculum service not available"
        )
    return curriculum_service_instance


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
            "tts_enabled": settings.tts_enabled,
            "development_mode": settings.is_development,
            "modular_generators": True  # NEW: Indicate modular architecture
        },
        "generator_status": {
            "master_context": "available",
            "reading_content": "available", 
            "visual_demo": "available",
            "audio_content": "available" if settings.tts_enabled else "disabled",
            "practice_problems": "available"
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
        # IMPROVED: Log grade information if available
        grade_info = getattr(request, 'grade', 'Not specified')
        logger.info(f"🎯 Content generation request: {request.subject}/{request.unit}/{request.skill}")
        logger.info(f"   Grade: {grade_info}, Difficulty: {request.difficulty_level}")
        
        # Generate content package (this will automatically store in cloud)
        package = await content_service.generate_content_package(request)
        
        logger.info(f"✅ Content package generated successfully: {package.id}")
        
        # FIXED: Use package.content instead of package.components
        content_count = len(package.content) if hasattr(package, 'content') and package.content else 0
        logger.info(f"   Content components generated: {content_count}")
        
        # Add background task for any cleanup if needed
        background_tasks.add_task(log_generation_complete, package.id, package.generation_metadata.generation_time_ms)
        
        return package
        
    except Exception as e:
        logger.error(f"❌ Content generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Content generation failed: {str(e)}"
        )


@app.post(f"{settings.API_V1_PREFIX}/generate-content-enhanced", response_model=ContentPackage)
async def generate_content_enhanced(
    request: EnhancedContentGenerationRequest,
    background_tasks: BackgroundTasks,
    content_service: ContentGenerationService = Depends(get_content_service),
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """Generate content using either curriculum reference or manual input - UPDATED WITH GRADE"""
    try:
        logger.info(f"🎯 Enhanced content generation request - Mode: {request.mode}")
        
        if request.mode == "curriculum":
            if not request.curriculum_request:
                raise HTTPException(status_code=400, detail="curriculum_request required for curriculum mode")
            
            # Get context from curriculum service - NOW INCLUDES GRADE
            context = curriculum_service.get_subskill_context(request.curriculum_request.subskill_id)
            
            # Convert to standard request format WITH GRADE
            standard_request = ContentGenerationRequest(
                subject=context["subject"],
                grade=context.get("grade"),  # IMPROVED: Use .get() for safer access
                unit=context["unit"],
                skill=context["skill"],
                subskill=context["subskill"],
                difficulty_level=request.curriculum_request.difficulty_level_override or context["difficulty_level"],
                prerequisites=request.curriculum_request.prerequisites_override or context["prerequisites"],
                custom_instructions=request.custom_instructions,
                content_types=request.content_types
            )
            
        elif request.mode == "manual":
            if not request.manual_request:
                raise HTTPException(status_code=400, detail="manual_request required for manual mode")
            
            # Convert manual request to standard format WITH GRADE
            standard_request = ContentGenerationRequest(
                subject=request.manual_request.subject,
                grade=getattr(request.manual_request, 'grade', None),
                unit=request.manual_request.unit,
                skill=request.manual_request.skill,
                subskill=request.manual_request.subskill,
                difficulty_level=request.manual_request.difficulty_level,
                prerequisites=request.manual_request.prerequisites,
                custom_instructions=request.custom_instructions,
                content_types=request.content_types
            )
        else:
            raise HTTPException(status_code=400, detail="Mode must be 'curriculum' or 'manual'")
        
        # IMPROVED: Better logging for enhanced generation
        grade_info = getattr(standard_request, 'grade', 'Not specified')
        logger.info(f"   Subject: {standard_request.subject}, Grade: {grade_info}")
        logger.info(f"   Subskill: {standard_request.subskill}")
        
        # Generate content package with grade information
        package = await content_service.generate_content_package(standard_request)
        
        logger.info(f"✅ Enhanced content package generated successfully: {package.id}")
        
        # FIXED: Use package.content instead of package.components
        # Count the number of content types in the content dictionary
        content_count = len(package.content) if hasattr(package, 'content') and package.content else 0
        logger.info(f"   Content components generated: {content_count}")
        
        # Add background task
        background_tasks.add_task(log_generation_complete, package.id, package.generation_metadata.generation_time_ms)
        
        return package
        
    except ValueError as e:
        logger.warning(f"⚠️ Invalid curriculum reference: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Enhanced content generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Enhanced content generation failed: {str(e)}"
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
        
        # FIXED: Use package.content instead of package.components
        if hasattr(package, 'content') and package.content:
            content_types = list(package.content.keys())
            logger.info(f"✅ Package retrieved: {package_id} with content types: {content_types}")
        else:
            logger.info(f"✅ Package retrieved: {package_id} (no content data)")
        
        return package
        
    except ValueError as e:
        logger.warning(f"⚠️ Package not found: {package_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to retrieve package {package_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content package")


@app.put(f"{settings.API_V1_PREFIX}/content/{{package_id}}/revise", response_model=ContentPackage)
async def revise_content_package(
    package_id: str,
    revision_request: RevisionRequest,
    background_tasks: BackgroundTasks,
    content_service: ContentGenerationService = Depends(get_content_service)
):
    """
    Revise specific components of a content package based on feedback
    
    This endpoint allows educators to request specific changes to individual 
    components (reading, visual, audio, practice) while maintaining coherence
    across the entire package.
    """
    try:
        component_types = [r.component_type.value for r in revision_request.revisions]
        logger.info(f"🔄 Content revision request for package: {package_id}")
        logger.info(f"   Components to revise: {component_types}")
        logger.info(f"   Reviewer: {revision_request.reviewer_id}")
        
        # Validate package_id matches request
        if package_id != revision_request.package_id:
            raise HTTPException(
                status_code=400, 
                detail="Package ID in URL must match package ID in request body"
            )
        
        # IMPROVED: Validate component types before processing
        valid_components = {"reading", "visual", "audio", "practice"}
        invalid_components = [ct for ct in component_types if ct not in valid_components]
        if invalid_components:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid component types: {invalid_components}. Must be one of: {valid_components}"
            )
        
        # Perform revision
        revised_package = await content_service.revise_content_package(
            package_id=revision_request.package_id,
            subject=revision_request.subject,
            unit=revision_request.unit,
            revisions=revision_request.revisions,
            reviewer_id=revision_request.reviewer_id
        )
        
        # Add background task
        background_tasks.add_task(
            log_revision_complete, 
            package_id, 
            component_types
        )
        
        logger.info(f"✅ Content revision completed for package: {package_id}")
        logger.info(f"   Revised components: {len(component_types)}")
        return revised_package
        
    except ValueError as e:
        logger.warning(f"⚠️ Revision request invalid: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Content revision failed for package {package_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Content revision failed: {str(e)}"
        )


# NEW: Endpoint to test individual generators
@app.post(f"{settings.API_V1_PREFIX}/test/generator/{{generator_type}}")
async def test_individual_generator(
    generator_type: str,
    request: ContentGenerationRequest,
    content_service: ContentGenerationService = Depends(get_content_service)
):
    """Test individual generators - useful for debugging and development"""
    try:
        valid_generators = {"master_context", "reading", "visual", "audio", "practice"}
        if generator_type not in valid_generators:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid generator type. Must be one of: {valid_generators}"
            )
        
        logger.info(f"🧪 Testing {generator_type} generator")
        
        # This would call specific generator test methods
        # Implementation depends on your ContentGenerationService structure
        result = await content_service.test_generator(generator_type, request)
        
        return {
            "generator_type": generator_type,
            "status": "success",
            "result": result,
            "test_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Generator test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Generator test failed: {str(e)}"
        )


@app.get(f"{settings.API_V1_PREFIX}/health")
async def health_check():
    """Comprehensive health check for all services"""
    try:
        logger.info("🏥 Running health check...")
        
        # Check storage services
        cosmos_health = await cosmos_service.health_check()
        blob_health = await blob_storage_service.health_check()
        
        # IMPROVED: Test individual generators
        generator_health = {}
        try:
            content_service = ContentGenerationService()
            generator_health = {
                "master_context": "available",
                "reading_content": "available",
                "visual_demo": "available",
                "audio_content": "available" if settings.tts_enabled else "disabled",
                "practice_problems": "available"
            }
        except Exception as e:
            generator_health = {"status": "error", "error": str(e)}
        
        # FIXED: Check curriculum service health
        curriculum_health = {}
        try:
            curriculum_service = get_curriculum_service()
            status = curriculum_service.get_status()
            curriculum_health = {
                "status": "loaded" if status.get("loaded", False) else "not_loaded",
                "total_records": status.get("statistics", {}).get("total_units", 0),
                "subjects": len(status.get("statistics", {}).get("subjects_grades", {}))
            }
        except Exception as e:
            curriculum_health = {"status": "error", "error": str(e)}
        
        # Determine overall health
        cosmos_healthy = cosmos_health.get("status") == "healthy"
        blob_healthy = blob_health.get("status") == "healthy"
        generators_healthy = isinstance(generator_health, dict) and "error" not in generator_health
        curriculum_available = curriculum_health.get("status") != "error"
        overall_healthy = cosmos_healthy and blob_healthy and generators_healthy and curriculum_available
        
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
                "content_generators": generator_health,
                "curriculum_service": curriculum_health,
                "features": {
                    "tts_enabled": settings.tts_enabled,
                    "blob_storage_enabled": settings.blob_storage_enabled,
                    "modular_architecture": True
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


# CURRICULUM ENDPOINTS - FIXED with singleton service
@app.post(f"{settings.API_V1_PREFIX}/curriculum/load")
async def load_curriculum_data(
    curriculum_file: UploadFile = File(...),
    learning_paths_file: Optional[UploadFile] = File(None),
    subskill_paths_file: Optional[UploadFile] = File(None),
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """Load curriculum data from uploaded files"""
    try:
        logger.info("📚 Loading curriculum data...")
        
        # Load main curriculum CSV
        csv_content = await curriculum_file.read()
        csv_text = csv_content.decode('utf-8')
        records_loaded = await curriculum_service.load_curriculum_from_csv(csv_text)
        
        # Load learning paths if provided
        learning_paths_loaded = 0
        if learning_paths_file:
            learning_paths_content = await learning_paths_file.read()
            learning_paths_text = learning_paths_content.decode('utf-8')
            await curriculum_service.load_learning_paths(learning_paths_text)
            learning_paths_data = json.loads(learning_paths_text)
            learning_paths_loaded = len(learning_paths_data.get("learning_path_decision_tree", {}))
        
        # Load subskill paths if provided
        subskill_paths_loaded = 0
        if subskill_paths_file:
            subskill_paths_content = await subskill_paths_file.read()
            subskill_paths_text = subskill_paths_content.decode('utf-8')
            await curriculum_service.load_subskill_paths(subskill_paths_text)
            subskill_paths_data = json.loads(subskill_paths_text)
            subskill_paths_loaded = len(subskill_paths_data.get("subskill_learning_path", {}))
        
        logger.info(f"✅ Curriculum loaded: {records_loaded} records, {learning_paths_loaded} learning paths, {subskill_paths_loaded} subskill paths")
        
        return {
            "status": "loaded",
            "curriculum_records": records_loaded,
            "learning_paths": learning_paths_loaded,
            "subskill_paths": subskill_paths_loaded,
            "subjects": curriculum_service.get_subjects()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to load curriculum: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to load curriculum: {str(e)}")


@app.get(f"{settings.API_V1_PREFIX}/curriculum/context/{{subskill_id}}")
async def get_curriculum_context(
    subskill_id: str,
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """Get detailed context for a specific subskill"""
    try:
        context = curriculum_service.get_subskill_context(subskill_id)
        return context
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to get context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get subskill context: {str(e)}")


# Background task functions
async def log_generation_complete(package_id: str, generation_time_ms: int):
    """Background task to log generation completion"""
    logger.info(f"📊 Package {package_id} generation completed in {generation_time_ms}ms")


async def log_revision_complete(package_id: str, revised_components: List[str]):
    """Background task to log revision completion"""
    logger.info(f"📊 Package {package_id} revision completed for components: {', '.join(revised_components)}")


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


@app.get(f"{settings.API_V1_PREFIX}/content/{{package_id}}/revisions")
async def get_package_revision_history(
    package_id: str, 
    subject: str, 
    unit: str,
    content_service: ContentGenerationService = Depends(get_content_service)
):
    """Get revision history for a specific package"""
    try:
        logger.info(f"📋 Getting revision history for package: {package_id}")
        
        package = await content_service.get_content_package(package_id, subject, unit)
        
        revision_history = package.revision_history if hasattr(package, 'revision_history') else []
        
        return {
            "package_id": package_id,
            "revision_count": len(revision_history),
            "revisions": revision_history,
            "current_status": package.status
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to get revision history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get revision history")


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


@app.get(f"{settings.API_V1_PREFIX}/curriculum/browse")
async def browse_curriculum(
    subject: Optional[str] = None, 
    grade: Optional[str] = None,
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """Browse curriculum structure with optional filtering"""
    try:
        curricula = curriculum_service.get_curriculum(subject=subject, grade=grade)
        
        if not curricula:
            raise HTTPException(status_code=404, detail="No curriculum found")
        
        return {
            "total_curricula": len(curricula),
            "filters": {"subject": subject, "grade": grade},
            "curricula": curricula
        }
    except Exception as e:
        logger.error(f"❌ Failed to browse curriculum: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to browse curriculum: {str(e)}")


@app.get(f"{settings.API_V1_PREFIX}/curriculum/status")
async def get_curriculum_status(
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """Get curriculum loading status and statistics"""
    try:
        return curriculum_service.get_status()
    except Exception as e:
        logger.error(f"❌ Failed to get status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get curriculum status")


@app.get(f"{settings.API_V1_PREFIX}/curriculum/subjects")
async def get_subjects(
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """Get list of available subjects"""
    try:
        subjects = curriculum_service.get_subjects()
        return {"subjects": subjects, "total": len(subjects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get subjects")


@app.get(f"{settings.API_V1_PREFIX}/curriculum/grades")
async def get_grades(
    subject: Optional[str] = None,
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """Get list of available grades"""
    try:
        grades = curriculum_service.get_grades(subject)
        return {"grades": grades, "subject_filter": subject, "total": len(grades)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get grades")


@app.get(f"{settings.API_V1_PREFIX}/curriculum/learning-path/{{skill_id}}")
async def get_learning_path(
    skill_id: str,
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """Get learning path for a specific skill"""
    try:
        path = curriculum_service.get_learning_path(skill_id)
        return {"skill_id": skill_id, "next_skills": path, "path_length": len(path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get learning path")


@app.get(f"{settings.API_V1_PREFIX}/curriculum/subskill-path/{{subskill_id}}")
async def get_subskill_path(
    subskill_id: str,
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """Get next subskill in the learning progression"""
    try:
        next_subskill = curriculum_service.get_next_subskill(subskill_id)
        return {
            "current_subskill": subskill_id,
            "next_subskill": next_subskill,
            "has_next": next_subskill is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get subskill path")


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