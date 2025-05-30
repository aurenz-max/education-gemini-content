# app/models/curriculum.py (or just curriculum.py)
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

@dataclass
class Subskill:
    subskill_id: str
    subskill_description: str
    difficulty_start: float
    difficulty_end: float
    target_difficulty: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass  
class Skill:
    skill_id: str
    skill_description: str
    subskills: List[Subskill]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "skill_description": self.skill_description,
            "subskills": [subskill.to_dict() for subskill in self.subskills]
        }

@dataclass
class Unit:
    unit_id: str
    unit_title: str
    skills: List[Skill]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "unit_title": self.unit_title,
            "skills": [skill.to_dict() for skill in self.skills]
        }

@dataclass
class Curriculum:
    subject: str
    grade: str
    units: List[Unit]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "grade": self.grade,
            "units": [unit.to_dict() for unit in self.units]
        }

# Pydantic models for API requests
class CurriculumReferenceRequest(BaseModel):
    """Request using curriculum reference for auto-population"""
    subskill_id: str
    auto_populate: bool = True
    difficulty_level_override: Optional[str] = None
    prerequisites_override: Optional[List[str]] = None

class ManualContentRequest(BaseModel):
    """Manual content generation request"""
    subject: str
    unit: str
    skill: str
    subskill: str
    difficulty_level: str
    prerequisites: List[str] = Field(default_factory=list)

class EnhancedContentGenerationRequest(BaseModel):
    """Enhanced request that supports both manual and curriculum reference modes"""
    mode: str = Field(..., description="Either 'manual' or 'curriculum'")
    manual_request: Optional[ManualContentRequest] = None
    curriculum_request: Optional[CurriculumReferenceRequest] = None
    custom_instructions: Optional[str] = None
    content_types: Optional[List[str]] = Field(default_factory=lambda: ["reading", "visual", "audio", "practice"])