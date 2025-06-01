# backend/app/core/content_generator.py
import asyncio
import logging
from datetime import datetime
from typing import List

from app.models.content import (
    ContentGenerationRequest, 
    ContentPackage,
    GenerationMetadata,
    ComponentRevision, 
    RevisionEntry,
    ComponentType
)

# Import all generators
from app.core.generators import (
    MasterContextGenerator,
    ReadingContentGenerator,
    VisualDemoGenerator,
    AudioContentGenerator,
    PracticeProblemsGenerator
)

# Import existing services
from app.database.cosmos_client import cosmos_service
from app.database.blob_storage import blob_storage_service
from app.config import settings

logger = logging.getLogger(__name__)

logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('azure.cosmos').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.WARNING)


class ContentGenerationService:
    """Main orchestrator for generating educational content using modular generators"""
    
    def __init__(self):
        # Initialize services
        self.cosmos_service = cosmos_service
        self.blob_service = blob_storage_service
        
        # Initialize all content generators
        self.master_context_generator = MasterContextGenerator(
            cosmos_service=self.cosmos_service,
            blob_service=self.blob_service
        )
        self.reading_generator = ReadingContentGenerator(
            cosmos_service=self.cosmos_service,
            blob_service=self.blob_service
        )
        self.visual_generator = VisualDemoGenerator(
            cosmos_service=self.cosmos_service,
            blob_service=self.blob_service
        )
        self.audio_generator = AudioContentGenerator(
            cosmos_service=self.cosmos_service,
            blob_service=self.blob_service
        )
        self.practice_generator = PracticeProblemsGenerator(
            cosmos_service=self.cosmos_service,
            blob_service=self.blob_service
        )
        
        logger.info(f"ContentGenerationService initialized with all generators (Environment: {settings.ENVIRONMENT})")
    
    async def generate_content_package(self, request: ContentGenerationRequest) -> ContentPackage:
        """Generate complete educational content package using modular generators"""
        
        start_time = datetime.now()
        package_id = f"pkg_{int(start_time.timestamp())}"
        
        try:
            logger.info(f"Starting content generation for {request.subject}/{request.skill}")
            
            # Generate master context with grade information
            master_context = await self.master_context_generator.generate_master_context(request)
            
            # Generate content components in parallel where possible
            reading_task = self.reading_generator.generate_reading_content(request, master_context, package_id)
            visual_task = self.visual_generator.generate_visual_demo(request, master_context, package_id)
            audio_script_task = self.audio_generator.generate_audio_script(request, master_context)
            
            reading_comp, visual_comp, audio_script = await asyncio.gather(
                reading_task, visual_task, audio_script_task
            )
            
            # Generate audio and upload to blob storage (conditional on TTS setting)
            audio_comp = await self.audio_generator.generate_and_store_audio(audio_script, package_id)
            
            # Generate practice problems (depends on reading and visual components)
            practice_comp = await self.practice_generator.generate_practice_problems(
                request, master_context, reading_comp, visual_comp, package_id
            )
            
            # Create package
            generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            package = ContentPackage(
                id=package_id,
                partition_key=f"{request.subject}-{request.unit}",
                subject=request.subject,
                unit=request.unit,
                skill=request.skill,
                subskill=request.subskill,
                master_context=master_context,
                content={
                    "reading": reading_comp.content,
                    "visual": visual_comp.content,
                    "audio": audio_comp.content,
                    "practice": practice_comp.content
                },
                generation_metadata=GenerationMetadata(
                    generation_time_ms=generation_time,
                    coherence_score=0.90
                )
            )
            
            # Store in Cosmos DB
            stored_package = await self.cosmos_service.create_content_package(package)
            
            logger.info(f"Content generation and storage completed in {generation_time}ms")
            return stored_package
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            await self._cleanup_on_failure(package_id)
            raise

    async def revise_content_package(
        self, 
        package_id: str, 
        subject: str, 
        unit: str,
        revisions: List[ComponentRevision],
        reviewer_id: str = None
    ) -> ContentPackage:
        """
        Revise specific components of a content package using appropriate generators
        
        Args:
            package_id: ID of package to revise  
            subject: Subject for partition key
            unit: Unit for partition key
            revisions: List of component revisions to apply
            reviewer_id: ID of reviewer requesting changes
            
        Returns:
            Updated ContentPackage with revised components
        """
        start_time = datetime.now()
        partition_key = f"{subject}-{unit}"
        
        try:
            logger.info(f"Starting revision for package {package_id}")
            logger.info(f"Components to revise: {[r.component_type.value for r in revisions]}")
            
            # Get existing package
            package = await self.cosmos_service.get_content_package(package_id, partition_key)
            if not package:
                raise ValueError(f"Package {package_id} not found")
            
            # Convert to dict for easier manipulation - use mode='json' to serialize datetime objects
            package_dict = package.model_dump(mode='json')
            
            # Process each revision using appropriate generators
            revision_entries = []
            for revision in revisions:
                logger.info(f"Revising {revision.component_type.value} component")
                
                revision_start_time = datetime.now()
                
                # Route revision to appropriate generator
                revised_content = await self._route_revision_to_generator(
                    component_type=revision.component_type,
                    original_content=package_dict["content"][revision.component_type.value],
                    feedback=revision.feedback,
                    master_context=package.master_context,
                    package_id=package_id
                )
                
                # Update the content
                package_dict["content"][revision.component_type.value] = revised_content
                
                # Track revision time
                revision_time = int((datetime.now() - revision_start_time).total_seconds() * 1000)
                
                # Create revision entry with proper datetime handling
                revision_entry = RevisionEntry(
                    component_type=revision.component_type,
                    feedback=revision.feedback,
                    reviewer_id=reviewer_id,
                    generation_time_ms=revision_time
                )
                revision_entries.append(revision_entry)
            
            # Update package metadata
            total_time = int((datetime.now() - start_time).total_seconds() * 1000)
            package_dict["status"] = "needs_review"  # Back to review after revision
            package_dict["updated_at"] = datetime.now().isoformat()  # Convert to string
            
            # Add revision history with proper datetime serialization
            if "revision_history" not in package_dict:
                package_dict["revision_history"] = []
            
            # Add new revision entries with explicit datetime handling
            for entry in revision_entries:
                # Convert the RevisionEntry to dict and ensure datetime serialization
                entry_dict = entry.model_dump()
                
                # Add timestamp if not present
                if "timestamp" not in entry_dict:
                    entry_dict["timestamp"] = datetime.now().isoformat()
                
                # Ensure all datetime fields are strings
                for key, value in entry_dict.items():
                    if isinstance(value, datetime):
                        entry_dict[key] = value.isoformat()
                
                package_dict["revision_history"].append(entry_dict)
            
            # Update generation metadata
            if "generation_metadata" not in package_dict:
                package_dict["generation_metadata"] = {}
            
            # Safely update generation metadata
            current_time = package_dict["generation_metadata"].get("generation_time_ms", 0)
            package_dict["generation_metadata"]["generation_time_ms"] = current_time + total_time
            
            # Ensure all datetime fields in the entire package are serialized
            package_dict = self._serialize_datetime_fields(package_dict)
            
            # Convert back to ContentPackage and update in database
            updated_package = ContentPackage(**package_dict)
            stored_package = await self.cosmos_service.update_content_package(updated_package)
            
            logger.info(f"Package revision completed in {total_time}ms")
            logger.info(f"Revised components: {[r.component_type.value for r in revisions]}")
            
            return stored_package
            
        except Exception as e:
            logger.error(f"Package revision failed: {str(e)}")
            # Clean up any uploaded files on failure (reuse existing cleanup)
            await self._cleanup_on_failure(package_id)
            raise

    async def _route_revision_to_generator(
        self,
        component_type: ComponentType,
        original_content: dict,
        feedback: str,
        master_context,
        package_id: str
    ) -> dict:
        """Route revision requests to the appropriate generator"""
        
        if component_type == ComponentType.READING:
            return await self.reading_generator.revise_reading_content(
                original_content, feedback, master_context
            )
        elif component_type == ComponentType.VISUAL:
            return await self.visual_generator.revise_visual_demo(
                original_content, feedback, master_context
            )
        elif component_type == ComponentType.AUDIO:
            return await self.audio_generator.revise_audio_content(
                original_content, feedback, master_context, package_id
            )
        elif component_type == ComponentType.PRACTICE:
            return await self.practice_generator.revise_practice_problems(
                original_content, feedback, master_context
            )
        else:
            raise ValueError(f"Unknown component type: {component_type}")

    async def _cleanup_on_failure(self, package_id: str):
        """Clean up any uploaded files if generation fails"""
        try:
            logger.info(f"Cleaning up failed package: {package_id}")
            cleanup_result = await self.blob_service.cleanup_package_audio(package_id)
            if cleanup_result["success"]:
                logger.info(f"Cleaned up {cleanup_result['deleted_count']} audio files")
            else:
                logger.warning(f"Cleanup had errors: {cleanup_result.get('errors', [])}")
        except Exception as e:
            logger.warning(f"Cleanup failed (non-critical): {str(e)}")

    def _serialize_datetime_fields(self, data):
        """
        Recursively convert all datetime objects to ISO format strings
        """
        if isinstance(data, dict):
            return {key: self._serialize_datetime_fields(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._serialize_datetime_fields(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data

    # Storage and retrieval methods (unchanged from original)
    async def get_content_package(self, package_id: str, subject: str, unit: str) -> ContentPackage:
        """Retrieve a content package from storage"""
        partition_key = f"{subject}-{unit}"
        package = await self.cosmos_service.get_content_package(package_id, partition_key)
        if not package:
            raise ValueError(f"Content package {package_id} not found")
        return package

    async def list_content_packages(self, subject: str = None, unit: str = None) -> list[ContentPackage]:
        """List content packages with optional filtering"""
        return await self.cosmos_service.list_content_packages(
            subject=subject,
            unit=unit,
            limit=100
        )

    async def delete_content_package(self, package_id: str, subject: str, unit: str) -> bool:
        """Delete a content package and clean up associated files"""
        partition_key = f"{subject}-{unit}"
        
        try:
            # Delete from Cosmos DB
            deleted = await self.cosmos_service.delete_content_package(package_id, partition_key)
            if not deleted:
                return False
            
            # Clean up blob storage
            cleanup_result = await self.blob_service.cleanup_package_audio(package_id)
            logger.info(f"Cleaned up {cleanup_result.get('deleted_count', 0)} audio files")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete package {package_id}: {str(e)}")
            return False