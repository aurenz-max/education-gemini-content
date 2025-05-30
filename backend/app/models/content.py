# backend/app/models/content.py - Updated with Revision Support AND Grade Integration
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class ContentStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    GENERATED = "generated"
    APPROVED = "approved"
    PUBLISHED = "published"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"


class ComponentType(str, Enum):
    READING = "reading"
    VISUAL = "visual"
    AUDIO = "audio"
    PRACTICE = "practice"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# NEW: Revision-specific models
class ComponentRevision(BaseModel):
    """Individual component revision request"""
    component_type: ComponentType = Field(..., description="Which component to revise")
    feedback: str = Field(..., description="Specific feedback for revision")
    priority: str = Field(default="medium", description="Revision priority")
    
    @validator('feedback')
    def validate_feedback(cls, v):
        if not v or not v.strip():
            raise ValueError("Feedback cannot be empty")
        return v.strip()


class RevisionRequest(BaseModel):
    """Request for revising content package components"""
    package_id: str = Field(..., description="Package ID to revise")
    subject: str = Field(..., description="Subject for partition key")
    unit: str = Field(..., description="Unit for partition key")
    revisions: List[ComponentRevision] = Field(..., description="Component revisions to apply")
    reviewer_id: Optional[str] = Field(None, description="ID of reviewer requesting changes")
    
    @validator('revisions')
    def validate_revisions(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one revision must be specified")
        
        # Check for duplicate component types
        component_types = [r.component_type for r in v]
        if len(component_types) != len(set(component_types)):
            raise ValueError("Cannot have multiple revisions for the same component type")
        
        return v


class RevisionEntry(BaseModel):
    """Individual revision history entry"""
    revision_id: str = Field(default_factory=lambda: f"rev_{int(datetime.utcnow().timestamp())}")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    component_type: ComponentType = Field(..., description="Component that was revised")
    feedback: str = Field(..., description="Feedback that triggered revision")
    status: str = Field(default="completed", description="Revision status")
    reviewer_id: Optional[str] = Field(None, description="Who requested the revision")
    generation_time_ms: Optional[int] = Field(None, description="Time taken for revision")


# Request Models - UPDATED WITH GRADE
class ContentGenerationRequest(BaseModel):
    subject: str = Field(..., description="Subject area (e.g., Mathematics)")
    grade: Optional[str] = Field(None, description="Grade level (e.g., Kindergarten, 1st Grade)")  # NEW FIELD
    unit: str = Field(..., description="Unit within subject (e.g., Algebra)")
    skill: str = Field(..., description="Specific skill (e.g., Linear Equations)")
    subskill: str = Field(..., description="Subskill (e.g., Slope-Intercept Form)")
    difficulty_level: DifficultyLevel = Field(default=DifficultyLevel.INTERMEDIATE)
    prerequisites: List[str] = Field(default=[], description="Required prior knowledge")
    educator_id: Optional[str] = Field(None, description="Requesting educator ID")
    priority: str = Field(default="medium", description="Generation priority")
    custom_instructions: Optional[str] = Field(None, description="Additional generation instructions")
    content_types: List[str] = Field(default=["reading", "visual", "audio", "practice"], description="Content types to generate")
    
    @validator('subject', 'unit', 'skill', 'subskill')
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


# Curriculum-specific request models - UPDATED WITH GRADE
class ManualContentRequest(BaseModel):
    """Manual content generation request - UPDATED WITH GRADE"""
    subject: str = Field(..., description="Subject area")
    grade: Optional[str] = Field(None, description="Grade level")  # NEW FIELD
    unit: str = Field(..., description="Unit within subject")
    skill: str = Field(..., description="Specific skill")
    subskill: str = Field(..., description="Subskill")
    difficulty_level: str = Field(..., description="Difficulty level")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites")


class CurriculumReferenceRequest(BaseModel):
    """Request using curriculum reference for auto-population"""
    subskill_id: str = Field(..., description="Subskill ID from curriculum")
    auto_populate: bool = Field(default=True, description="Auto-populate from curriculum")
    difficulty_level_override: Optional[str] = Field(None, description="Override difficulty level")
    prerequisites_override: Optional[List[str]] = Field(None, description="Override prerequisites")


class EnhancedContentGenerationRequest(BaseModel):
    """Enhanced request that supports both manual and curriculum reference modes"""
    mode: str = Field(..., description="Either 'manual' or 'curriculum'")
    manual_request: Optional[ManualContentRequest] = Field(None, description="Manual generation request")
    curriculum_request: Optional[CurriculumReferenceRequest] = Field(None, description="Curriculum reference request")
    custom_instructions: Optional[str] = Field(None, description="Additional instructions")
    content_types: Optional[List[str]] = Field(default=["reading", "visual", "audio", "practice"], description="Content types to generate")


# Core Content Models - UPDATED WITH GRADE
class MasterContext(BaseModel):
    core_concepts: List[str] = Field(..., description="Key concepts to be taught")
    key_terminology: Dict[str, str] = Field(..., description="Term definitions")
    learning_objectives: List[str] = Field(..., description="What students should learn")
    difficulty_level: str = Field(..., description="Content difficulty")
    grade_level: Optional[str] = Field(None, description="Target grade level")  # NEW FIELD
    prerequisites: List[str] = Field(..., description="Required prior knowledge")
    real_world_applications: List[str] = Field(default=[], description="Practical applications")


class CoherenceMarkers(BaseModel):
    referenced_terms: List[str] = Field(default=[], description="Terms referenced in content")
    concepts_reinforced: List[str] = Field(default=[], description="Concepts reinforced")
    cross_references: List[str] = Field(default=[], description="References to other content")


class ContentComponent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    package_id: str = Field(..., description="Parent content package ID")
    component_type: ComponentType = Field(..., description="Type of content component")
    content: Dict[str, Any] = Field(..., description="Component-specific content")
    metadata: Dict[str, Any] = Field(default={}, description="Component metadata")
    coherence_markers: CoherenceMarkers = Field(default=CoherenceMarkers())
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GenerationMetadata(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(default="gemini-2.5-flash-preview-05-20")
    generation_time_ms: int = Field(..., description="Generation time in milliseconds")
    coherence_score: float = Field(default=0.0, description="Overall coherence score 0-1")
    validation_passed: bool = Field(default=True)
    retry_count: int = Field(default=0, description="Number of generation retries")
    
    @validator('coherence_score')
    def validate_coherence_score(cls, v):
        if v < 0 or v > 1:
            raise ValueError("Coherence score must be between 0 and 1")
        return v


class ContentPackage(BaseModel):
    # Core identification
    id: str = Field(..., description="Package ID (e.g., pkg_1748053402)")
    
    # Content identification - UPDATED WITH GRADE
    subject: str = Field(..., description="Subject area")
    grade: Optional[str] = Field(None, description="Grade level")  # NEW FIELD
    unit: str = Field(..., description="Unit within subject")
    skill: str = Field(..., description="Specific skill")
    subskill: str = Field(..., description="Subskill")
    
    # Master context for coherence
    master_context: MasterContext = Field(..., description="Master context for coherence")
    
    # Content structure
    content: Dict[str, Any] = Field(..., description="Embedded content components")
    
    # Generation information
    generation_metadata: GenerationMetadata = Field(..., description="Generation information")
    
    # Cosmos DB specific fields
    partition_key: Optional[str] = Field(None, description="Partition key for Cosmos DB")
    document_type: Optional[str] = Field(None, description="Document type identifier")
    
    # Status and workflow
    status: str = Field(default="generated", description="Package status")
    created_by: Optional[str] = Field(None, description="Creator ID")
    
    # Component IDs (optional, for complex setups)
    content_ids: Dict[str, str] = Field(default={}, description="IDs of content components")
    
    # Review information
    review_status: str = Field(default="pending", description="Review status")
    reviewed_by: Optional[str] = Field(None, description="Reviewer ID")
    reviewed_at: Optional[str] = Field(None, description="Review timestamp as ISO string")
    review_notes: List[Dict[str, Any]] = Field(default=[], description="Review feedback as objects")
    
    # NEW: Revision history
    revision_history: List[RevisionEntry] = Field(default=[], description="History of revisions made")
    
    # Timestamps
    created_at: Optional[str] = Field(None, description="Creation timestamp as ISO string")
    updated_at: Optional[str] = Field(None, description="Last update timestamp as ISO string")
    
    def __init__(self, **data):
        # Automatically generate partition_key if not provided
        if 'partition_key' not in data and 'subject' in data and 'unit' in data:
            data['partition_key'] = f"{data['subject']}-{data['unit']}"
        
        # Set timestamps if not provided
        current_time = datetime.utcnow().isoformat()
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = current_time
        if 'updated_at' not in data or data['updated_at'] is None:
            data['updated_at'] = current_time
            
        super().__init__(**data)
    
    @validator('content')
    def validate_content_structure(cls, v):
        """Validate that content has required components"""
        required_components = ['reading', 'visual', 'audio', 'practice']
        for component in required_components:
            if component not in v:
                raise ValueError(f"Content must include {component} component")
        return v


# Generation Progress Tracking
class GenerationProgress(BaseModel):
    package_id: str
    status: str = Field(default="starting")
    current_stage: str = Field(default="master_context")
    stages_completed: List[str] = Field(default=[])
    stages_remaining: List[str] = Field(default=[
        "master_context", "reading", "visual", "audio_script", 
        "audio_tts", "practice", "validation"
    ])
    estimated_completion_time: Optional[datetime] = Field(None)
    error_message: Optional[str] = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Batch Generation Request - UPDATED WITH GRADE
class BatchGenerationRequest(BaseModel):
    requests: List[ContentGenerationRequest] = Field(..., description="Multiple content requests")
    batch_name: Optional[str] = Field(None, description="Batch identifier")
    priority: str = Field(default="medium")
    target_grade: Optional[str] = Field(None, description="Target grade for all requests in batch")  # NEW FIELD
    
    @validator('requests')
    def validate_batch_size(cls, v):
        if len(v) > 10:
            raise ValueError("Batch size cannot exceed 10 requests")
        if len(v) == 0:
            raise ValueError("Batch must contain at least 1 request")
        return v


# Storage Metadata (added during Cosmos DB operations)
class StorageMetadata(BaseModel):
    created_at: str = Field(..., description="ISO timestamp when stored")
    updated_at: str = Field(..., description="ISO timestamp when last updated")
    version: int = Field(default=1, description="Document version number")
    content_hash: str = Field(..., description="SHA256 hash of content for integrity")
    revision_history: List[RevisionEntry] = Field(default=[], description="Revision history")


# Review Queue Entry (for educator workflow) - UPDATED WITH GRADE
class ReviewQueueEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    package_id: str = Field(..., description="Content package ID to review")
    grade_level: Optional[str] = Field(None, description="Grade level of content")  # NEW FIELD
    educator_id: str = Field(..., description="Assigned educator ID")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    priority: str = Field(default="medium", description="Review priority")
    estimated_review_time: int = Field(default=15, description="Estimated minutes to review")
    review_type: str = Field(default="initial", description="Type of review")
    due_date: Optional[datetime] = Field(None, description="Review due date")
    status: str = Field(default="assigned", description="Review status")