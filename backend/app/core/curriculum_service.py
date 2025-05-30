# app/core/curriculum_service.py (FIXED PATH)
import pandas as pd
import io
import json
from typing import List, Optional, Dict, Any

from app.models.curriculum import Subskill, Skill, Unit, Curriculum

class CurriculumService:
    def __init__(self):
        self.curriculum_data: Dict[str, Dict[str, Curriculum]] = {}
        self.learning_paths: Dict[str, List[str]] = {}
        self.subskill_paths: Dict[str, str] = {}
    
    async def load_curriculum_from_csv(self, csv_content: str) -> int:
        """Load curriculum data from CSV content"""
        try:
            df = pd.read_csv(io.StringIO(csv_content))
            
            # Group by subject and grade
            for subject in df['Subject'].unique():
                if subject not in self.curriculum_data:
                    self.curriculum_data[subject] = {}
                
                subject_df = df[df['Subject'] == subject]
                
                for grade in subject_df['Grade'].unique():
                    grade_df = subject_df[subject_df['Grade'] == grade]
                    
                    # Build units
                    units = []
                    for unit_id in grade_df['UnitID'].unique():
                        unit_df = grade_df[grade_df['UnitID'] == unit_id]
                        unit_title = unit_df['UnitTitle'].iloc[0]
                        
                        # Build skills
                        skills = []
                        for skill_id in unit_df['SkillID'].unique():
                            skill_df = unit_df[unit_df['SkillID'] == skill_id]
                            skill_description = skill_df['SkillDescription'].iloc[0]
                            
                            # Build subskills
                            subskills = []
                            for _, row in skill_df.iterrows():
                                subskill = Subskill(
                                    subskill_id=row['SubskillID'],
                                    subskill_description=row['SubskillDescription'],
                                    difficulty_start=float(row['DifficultyStart']),
                                    difficulty_end=float(row['DifficultyEnd']),
                                    target_difficulty=float(row['TargetDifficulty'])
                                )
                                subskills.append(subskill)
                            
                            skill = Skill(
                                skill_id=skill_id,
                                skill_description=skill_description,
                                subskills=subskills
                            )
                            skills.append(skill)
                        
                        unit = Unit(
                            unit_id=unit_id,
                            unit_title=unit_title,
                            skills=skills
                        )
                        units.append(unit)
                    
                    curriculum = Curriculum(
                        subject=subject,
                        grade=grade,
                        units=units
                    )
                    self.curriculum_data[subject][grade] = curriculum
            
            return len(df)
            
        except Exception as e:
            raise ValueError(f"Failed to parse curriculum CSV: {str(e)}")
    
    async def load_learning_paths(self, learning_paths_content: str):
        """Load learning path decision trees from JSON"""
        try:
            data = json.loads(learning_paths_content)
            self.learning_paths = data.get("learning_path_decision_tree", {})
        except Exception as e:
            raise ValueError(f"Failed to parse learning paths JSON: {str(e)}")
    
    async def load_subskill_paths(self, subskill_paths_content: str):
        """Load subskill learning paths from JSON"""
        try:
            data = json.loads(subskill_paths_content)
            paths = data.get("subskill_learning_path", {})
            self.subskill_paths = {
                subskill_id: path_info.get("next_subskill") 
                for subskill_id, path_info in paths.items()
                if path_info.get("next_subskill")
            }
        except Exception as e:
            raise ValueError(f"Failed to parse subskill paths JSON: {str(e)}")
    
    def get_curriculum(self, subject: str = None, grade: str = None) -> List[Dict]:
        """Get curriculum data with optional filtering"""
        result = []
        
        for subj, grades in self.curriculum_data.items():
            if subject and subj != subject:
                continue
                
            for gr, curriculum in grades.items():
                if grade and gr != grade:
                    continue
                
                result.append(curriculum.to_dict())
        
        return result
    
    def get_subskill_context(self, subskill_id: str) -> Dict[str, Any]:
        """Get context information for a specific subskill"""
        for subject, grades in self.curriculum_data.items():
            for grade, curriculum in grades.items():
                for unit in curriculum.units:
                    for skill in unit.skills:
                        for subskill in skill.subskills:
                            if subskill.subskill_id == subskill_id:
                                return {
                                    "subject": subject,
                                    "grade": grade,
                                    "unit": unit.unit_title,
                                    "skill": skill.skill_description,
                                    "subskill": subskill.subskill_description,
                                    "subskill_id": subskill_id,
                                    "difficulty_level": self._get_difficulty_level(subskill.target_difficulty),
                                    "target_difficulty": subskill.target_difficulty,
                                    "difficulty_range": {
                                        "start": subskill.difficulty_start,
                                        "end": subskill.difficulty_end
                                    },
                                    "prerequisites": self._get_prerequisites(subskill_id),
                                    "next_subskill": self.subskill_paths.get(subskill_id),
                                    "learning_path": self.learning_paths.get(skill.skill_id, [])
                                }
        
        raise ValueError(f"Subskill {subskill_id} not found")
    
    def get_status(self) -> Dict[str, Any]:
        """Get curriculum loading status and statistics"""
        total_subskills = 0
        total_skills = 0
        total_units = 0
        subjects_grades = []
        sample_subskills = []
        
        for subject, grades in self.curriculum_data.items():
            for grade, curriculum in grades.items():
                subjects_grades.append(f"{subject} - {grade}")
                total_units += len(curriculum.units)
                
                for unit in curriculum.units:
                    total_skills += len(unit.skills)
                    for skill in unit.skills:
                        total_subskills += len(skill.subskills)
                        # Collect sample subskills
                        for subskill in skill.subskills:
                            if len(sample_subskills) < 10:
                                sample_subskills.append(subskill.subskill_id)
        
        return {
            "loaded": len(self.curriculum_data) > 0,
            "statistics": {
                "subjects_grades": subjects_grades,
                "total_units": total_units,
                "total_skills": total_skills,
                "total_subskills": total_subskills,
                "learning_paths": len(self.learning_paths),
                "subskill_paths": len(self.subskill_paths)
            },
            "sample_subskills": sample_subskills
        }
    
    def get_subjects(self) -> List[str]:
        """Get list of available subjects"""
        return list(self.curriculum_data.keys())
    
    def get_grades(self, subject: str = None) -> List[str]:
        """Get list of available grades, optionally filtered by subject"""
        grades = set()
        
        for subj, grade_dict in self.curriculum_data.items():
            if subject and subj != subject:
                continue
            grades.update(grade_dict.keys())
        
        return sorted(list(grades))
    
    def get_learning_path(self, skill_id: str) -> List[str]:
        """Get learning path for a specific skill"""
        return self.learning_paths.get(skill_id, [])
    
    def get_next_subskill(self, subskill_id: str) -> Optional[str]:
        """Get next subskill in the learning progression"""
        return self.subskill_paths.get(subskill_id)
    
    def _get_prerequisites(self, subskill_id: str) -> List[str]:
        """Get prerequisites for a subskill based on learning paths"""
        prerequisites = []
        
        # Look for skills that lead to this subskill
        for skill_id, next_skills in self.learning_paths.items():
            if any(subskill_id.startswith(next_skill) for next_skill in next_skills):
                prerequisites.append(skill_id)
        
        # Also check subskill paths for direct prerequisites
        for prev_subskill, next_subskill in self.subskill_paths.items():
            if next_subskill == subskill_id:
                prerequisites.append(prev_subskill)
        
        return prerequisites
    
    def _get_difficulty_level(self, target_difficulty: float) -> str:
        """Convert numeric difficulty to descriptive level"""
        if target_difficulty <= 2:
            return "beginner"
        elif target_difficulty <= 4:
            return "intermediate"
        else:
            return "advanced"