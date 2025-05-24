# backend/app/models/content.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class ContentStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    APPROVED = "approved"
    PUBLISHED = "published"
    NEEDS_REVISION = "needs_revision"


class ComponentType(str, Enum):
    READING = "reading"
    VISUAL = "visual"
    AUDIO = "audio"
    PRACTICE = "practice"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# Request Models
class ContentGenerationRequest(BaseModel):
    subject: str = Field(..., description="Subject area (e.g., Mathematics)")
    unit: str = Field(..., description="Unit within subject (e.g., Algebra)")
    skill: str = Field(..., description="Specific skill (e.g., Linear Equations)")
    subskill: str = Field(..., description="Subskill (e.g., Slope-Intercept Form)")
    difficulty_level: DifficultyLevel = Field(default=DifficultyLevel.INTERMEDIATE)
    prerequisites: List[str] = Field(default=[], description="Required prior knowledge")
    educator_id: Optional[str] = Field(None, description="Requesting educator ID")
    priority: str = Field(default="medium", description="Generation priority")
    
    @validator('subject', 'unit', 'skill', 'subskill')
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


# Core Content Models
class MasterContext(BaseModel):
    core_concepts: List[str] = Field(..., description="Key concepts to be taught")
    key_terminology: Dict[str, str] = Field(..., description="Term definitions")
    learning_objectives: List[str] = Field(..., description="What students should learn")
    difficulty_level: str = Field(..., description="Content difficulty")
    prerequisites: List[str] = Field(..., description="Required prior knowledge")
    real_world_applications: List[str] = Field(default=[], description="Practical applications")
    
    class Config:
        schema_extra = {
            "example": {
                "core_concepts": ["slope", "y-intercept", "linear relationship"],
                "key_terminology": {
                    "slope": "rate of change between two points",
                    "y-intercept": "point where line crosses y-axis"
                },
                "learning_objectives": [
                    "Calculate slope from two points",
                    "Identify y-intercept from equation"
                ],
                "difficulty_level": "intermediate",
                "prerequisites": ["basic_algebra", "coordinate_plane"],
                "real_world_applications": [
                    "Calculating speed from distance graphs",
                    "Business cost analysis"
                ]
            }
        }


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
    
    class Config:
        schema_extra = {
            "example": {
                "component_type": "reading",
                "content": {
                    "title": "Understanding Slope-Intercept Form",
                    "sections": [
                        {
                            "heading": "What is Slope?",
                            "content": "Slope represents the rate of change...",
                            "key_terms_used": ["slope", "rate of change"]
                        }
                    ],
                    "word_count": 1200
                },
                "metadata": {
                    "word_count": 1200,
                    "reading_level": "grade-9",
                    "section_count": 4
                }
            }
        }


class GenerationMetadata(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(default="gemini-2.0-flash-001")
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
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    partition_key: str = Field(..., description="Partition key for Cosmos DB")
    
    # Content identification
    subject: str = Field(..., description="Subject area")
    unit: str = Field(..., description="Unit within subject")
    skill: str = Field(..., description="Specific skill")
    subskill: str = Field(..., description="Subskill")
    
    # Status and workflow
    status: ContentStatus = Field(default=ContentStatus.DRAFT)
    created_by: Optional[str] = Field(None, description="Creator ID")
    
    # Content structure
    master_context: Optional[MasterContext] = Field(None, description="Master context for coherence")
    content_ids: Dict[str, str] = Field(default={}, description="IDs of content components")
    
    # Generation information
    generation_metadata: Optional[GenerationMetadata] = Field(None, description="Generation information")
    
    # Embedded content (simplified storage)
    content: Dict[str, Any] = Field(default={}, description="Embedded content components")
    
    # Review information (simplified)
    review_status: str = Field(default="pending", description="Review status")
    reviewed_by: Optional[str] = Field(None, description="Reviewer ID")
    reviewed_at: Optional[datetime] = Field(None, description="Review timestamp")
    review_notes: List[str] = Field(default=[], description="Review feedback")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "subject": "Mathematics",
                "unit": "Algebra",
                "skill": "Linear Equations",
                "subskill": "Slope-Intercept Form",
                "status": "approved",
                "content": {
                    "reading": {
                        "title": "Understanding Slope-Intercept Form",
                        "word_count": 1200
                    },
                    "visual": {
                        "description": "Interactive line graphing tool",
                        "code_lines": 127
                    },
                    "audio": {
                        "audio_file_path": "generated_audio/audio_123.wav",
                        "duration_seconds": 245
                    },
                    "practice": {
                        "problem_count": 8,
                        "estimated_time_minutes": 15
                    }
                }
            }
        }


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


# Batch Generation Request
class BatchGenerationRequest(BaseModel):
    requests: List[ContentGenerationRequest] = Field(..., description="Multiple content requests")
    batch_name: Optional[str] = Field(None, description="Batch identifier")
    priority: str = Field(default="medium")
    
    @validator('requests')
    def validate_batch_size(cls, v):
        if len(v) > 10:
            raise ValueError("Batch size cannot exceed 10 requests")
        if len(v) == 0:
            raise ValueError("Batch must contain at least 1 request")
        return v