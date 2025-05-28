# backend/app/models/content.py - Updated with Cosmos DB integration
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class ContentStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    GENERATED = "generated"  # Added to match your system
    APPROVED = "approved"
    PUBLISHED = "published"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"  # Added for review workflow


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
                "core_concepts": [
                    "The structure and components of the slope-intercept form (y = mx + b).",
                    "Understanding 'm' as the slope, representing the rate of change and steepness of the line (rise over run).",
                    "Understanding 'b' as the y-intercept, representing the point where the line crosses the y-axis (the starting value when x=0)."
                ],
                "key_terminology": {
                    "Linear Equation": "An equation whose graph is a straight line.",
                    "Slope-Intercept Form": "A specific way to write linear equations, y = mx + b",
                    "Slope": "A measure of the steepness and direction of a line",
                    "Y-intercept": "The point where a line crosses the y-axis"
                },
                "learning_objectives": [
                    "Students will be able to identify the slope and y-intercept directly from a linear equation written in slope-intercept form.",
                    "Students will be able to graph a linear equation given in slope-intercept form by accurately plotting the y-intercept and using the slope to find additional points."
                ],
                "difficulty_level": "intermediate",
                "prerequisites": ["basic_algebra", "coordinate_plane"],
                "real_world_applications": [
                    "Modeling costs: Calculating the total cost of a service (e.g., cell phone plan, taxi fare) that includes a fixed initial fee (y-intercept) and a per-unit charge (slope).",
                    "Distance-time relationships: Representing constant speed (slope) and an initial starting position (y-intercept) in movement problems."
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
                            "key_terms_used": ["slope", "rate of change"],
                            "concepts_covered": ["slope definition"]
                        }
                    ],
                    "word_count": 1200,
                    "reading_level": "Intermediate"
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
    # Core identification - using your existing structure
    id: str = Field(..., description="Package ID (e.g., pkg_1748053402)")
    
    # Content identification
    subject: str = Field(..., description="Subject area")
    unit: str = Field(..., description="Unit within subject")
    skill: str = Field(..., description="Specific skill")
    subskill: str = Field(..., description="Subskill")
    
    # Master context for coherence - required in your structure
    master_context: MasterContext = Field(..., description="Master context for coherence")
    
    # Content structure - your existing embedded format
    content: Dict[str, Any] = Field(..., description="Embedded content components")
    
    # Generation information - required in your structure
    generation_metadata: GenerationMetadata = Field(..., description="Generation information")
    
    # Cosmos DB specific fields (optional, added during storage)
    partition_key: Optional[str] = Field(None, description="Partition key for Cosmos DB")
    document_type: Optional[str] = Field(None, description="Document type identifier")
    
    # Status and workflow - FIXED: Using string instead of enum for compatibility
    status: str = Field(default="generated", description="Package status")
    created_by: Optional[str] = Field(None, description="Creator ID")
    
    # Component IDs (optional, for complex setups)
    content_ids: Dict[str, str] = Field(default={}, description="IDs of content components")
    
    # Review information - FIXED: review_notes as List[Dict] to match API usage
    review_status: str = Field(default="pending", description="Review status")
    reviewed_by: Optional[str] = Field(None, description="Reviewer ID")
    reviewed_at: Optional[str] = Field(None, description="Review timestamp as ISO string")
    review_notes: List[Dict[str, Any]] = Field(default=[], description="Review feedback as objects")
    
    # Timestamps - FIXED: Using Optional[str] for better serialization
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
    
    class Config:
        schema_extra = {
            "example": {
                "id": "pkg_1748053402",
                "subject": "Mathematics",
                "unit": "Algebra",
                "skill": "Linear Equations",
                "subskill": "Slope-Intercept Form",
                "status": "generated",
                "master_context": {
                    "core_concepts": [
                        "The structure and components of the slope-intercept form (y = mx + b)"
                    ],
                    "key_terminology": {
                        "Linear Equation": "An equation whose graph is a straight line"
                    },
                    "learning_objectives": [
                        "Students will be able to identify the slope and y-intercept"
                    ],
                    "difficulty_level": "intermediate",
                    "prerequisites": ["basic_algebra"],
                    "real_world_applications": ["Modeling costs"]
                },
                "content": {
                    "reading": {
                        "title": "Understanding Slope-Intercept Form",
                        "sections": [
                            {
                                "heading": "Introduction",
                                "content": "Linear equations are...",
                                "key_terms_used": ["Linear Equation"],
                                "concepts_covered": ["introduction"]
                            }
                        ],
                        "word_count": 1150,
                        "reading_level": "Intermediate"
                    },
                    "visual": {
                        "p5_code": "function setup() { createCanvas(800, 600); }",
                        "description": "Interactive slope-intercept demonstration",
                        "interactive_elements": ["slope_slider", "y_intercept_slider"],
                        "concepts_demonstrated": ["slope", "y-intercept"],
                        "user_instructions": "Adjust sliders to see effects"
                    },
                    "audio": {
                        "audio_file_path": "generated_audio/audio_pkg_1748053402.wav",
                        "audio_filename": "audio_pkg_1748053402.wav",
                        "dialogue_script": "Teacher: Today we'll learn about...",
                        "duration_seconds": 356.4,
                        "voice_config": {
                            "teacher_voice": "Zephyr",
                            "student_voice": "Puck"
                        },
                        "tts_status": "success"
                    },
                    "practice": {
                        "problems": [
                            {
                                "id": "Mathematics_SKILL-01_SUBSKILL-01-A_timestamp_uuid",
                                "problem_data": {
                                    "problem_type": "Multiple Choice",
                                    "problem": "What is the slope of y = 2x + 3?",
                                    "answer": "2",
                                    "success_criteria": ["Identify slope coefficient"],
                                    "teaching_note": "Slope is coefficient of x",
                                    "metadata": {
                                        "subject": "Mathematics",
                                        "unit": {"id": "ALGEBRA001", "title": "Algebra"},
                                        "skill": {"id": "ALGEBRA001-01", "description": "Linear Equations"},
                                        "subskill": {"id": "ALGEBRA001-01-A", "description": "Slope-Intercept Form"}
                                    }
                                }
                            }
                        ],
                        "problem_count": 9,
                        "estimated_time_minutes": 18
                    }
                },
                "generation_metadata": {
                    "generation_time_ms": 241507,
                    "coherence_score": 0.9
                },
                "review_notes": [
                    {
                        "note": "Content looks good overall",
                        "status": "approved", 
                        "timestamp": "2025-05-27T12:00:00Z",
                        "reviewer_id": "educator_123"
                    }
                ]
            }
        }
    
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


# Storage Metadata (added during Cosmos DB operations)
class StorageMetadata(BaseModel):
    created_at: str = Field(..., description="ISO timestamp when stored")
    updated_at: str = Field(..., description="ISO timestamp when last updated")
    version: int = Field(default=1, description="Document version number")
    content_hash: str = Field(..., description="SHA256 hash of content for integrity")


# Review Queue Entry (for educator workflow)
class ReviewQueueEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    package_id: str = Field(..., description="Content package ID to review")
    educator_id: str = Field(..., description="Assigned educator ID")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    priority: str = Field(default="medium", description="Review priority")
    estimated_review_time: int = Field(default=15, description="Estimated minutes to review")
    review_type: str = Field(default="initial", description="Type of review")
    due_date: Optional[datetime] = Field(None, description="Review due date")
    status: str = Field(default="assigned", description="Review status")
    
    class Config:
        schema_extra = {
            "example": {
                "package_id": "pkg_1748053402",
                "educator_id": "educator_123",
                "priority": "high",
                "estimated_review_time": 20,
                "review_type": "initial"
            }
        }# backend/app/models/content.py - Updated to match your exact structure
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class MasterContext(BaseModel):
    """Master context that ensures coherence across all content types"""
    core_concepts: List[str]
    key_terminology: Dict[str, str]
    learning_objectives: List[str]
    difficulty_level: str
    prerequisites: List[str]
    real_world_applications: List[str]


class GenerationMetadata(BaseModel):
    """Metadata about the content generation process"""
    generation_time_ms: int
    coherence_score: float


class ContentPackage(BaseModel):
    """Complete educational content package matching your exact structure"""
    id: str
    subject: str
    unit: str
    skill: str
    subskill: str
    master_context: MasterContext
    content: Dict[str, Any]  # Contains reading, visual, audio, practice
    generation_metadata: GenerationMetadata
    
    # Optional fields that might be added during storage
    partition_key: Optional[str] = None
    
    def __init__(self, **data):
        # Automatically generate partition_key if not provided
        if 'partition_key' not in data and 'subject' in data and 'unit' in data:
            data['partition_key'] = f"{data['subject']}-{data['unit']}"
        super().__init__(**data)


class ContentGenerationRequest(BaseModel):
    """Request for generating educational content"""
    subject: str
    unit: str
    skill: str
    subskill: str
    difficulty_level: str = "intermediate"
    prerequisites: List[str] = []


class ComponentType(str, Enum):
    """Types of content components"""
    READING = "reading"
    VISUAL = "visual"
    AUDIO = "audio"
    PRACTICE = "practice"


class ContentComponent(BaseModel):
    """Individual content component (for internal use)"""
    package_id: str
    component_type: ComponentType
    content: Dict[str, Any]
    metadata: Dict[str, Any] = {}