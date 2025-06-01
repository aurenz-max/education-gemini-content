# backend/app/core/generators/practice_problems.py
import json
import logging
from datetime import datetime
from typing import Dict, Any
from google.genai.types import GenerateContentConfig

from .base_generator import BaseContentGenerator
from app.models.content import ContentGenerationRequest, MasterContext, ContentComponent, ComponentType
from app.core.schemas import PRACTICE_PROBLEMS_SCHEMA

logger = logging.getLogger(__name__)


class PracticeProblemsGenerator(BaseContentGenerator):
    """Generator for practice problems and assessments"""
    
    async def generate_practice_problems(
        self, 
        request: ContentGenerationRequest,
        master_context: MasterContext,
        reading_comp: ContentComponent,
        visual_comp: ContentComponent,
        package_id: str
    ) -> ContentComponent:
        """Generate practice problems integrating all content - UPDATED WITH GRADE"""
        
        reading_concepts = [concept for section in reading_comp.content.get('sections', []) 
                          for concept in section.get('concepts_covered', [])]
        visual_elements = visual_comp.content.get('interactive_elements', [])
        grade_info = self._extract_grade_info(request)
        
        prompt = f"""
        Create practice problems for {grade_info} students learning {request.subskill} that integrate multiple learning modes.

        Target Audience: {grade_info} students
        Subject: {request.subject}

        Master Context:
        Key Terms: {', '.join(master_context.key_terminology.keys())}
        Learning Objectives: {', '.join(master_context.learning_objectives)}

        Content Integration:
        Reading covered: {', '.join(reading_concepts)}
        Visual demo includes: {', '.join(visual_elements)}

        Generate 8-10 problems that:
        1. Test understanding of key terms using {grade_info} appropriate language
        2. Reference the visual demonstration in ways {grade_info} students understand
        3. Progress from basic to applied difficulty suitable for {grade_info}
        4. Include real-world applications relevant to {grade_info} experience
        5. Require integrated understanding at {grade_info} cognitive level
        6. Use problem formats familiar to {grade_info} students
        7. Include encouraging, positive language
        8. Have clear, simple instructions

        Grade-specific considerations for {grade_info}:
        - Use vocabulary and sentence structures appropriate for {grade_info}
        - Include visual or concrete examples when possible
        - Make instructions clear and step-by-step
        - Use familiar contexts and scenarios
        - Provide positive, encouraging feedback criteria

        For each problem, provide:
        - problem_type: (e.g., "Multiple Choice", "Problem Solving", "Drawing/Visual", "Real-World Application")
        - problem: The actual question/problem statement (written for {grade_info})
        - answer: The correct answer or solution
        - success_criteria: Array of 2-3 criteria that define successful completion for {grade_info}
        - teaching_note: Helpful note for educators about teaching this concept to {grade_info}
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=PRACTICE_PROBLEMS_SCHEMA,
                    temperature=0.5,
                    max_output_tokens=16000
                )
            )
            
            problems_data = self._safe_json_loads(response.text, "Practice problems generation")
            
            # Convert to your required format with grade information
            formatted_problems = []
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            
            for i, problem in enumerate(problems_data.get('problems', [])):
                problem_uuid = __import__('uuid').uuid4()
                
                problem_id = f"{request.subject}_SKILL-{i+1:02d}_SUBSKILL-{i+1:02d}-A_{timestamp}_{problem_uuid}"
                difficulty = round(3.0 + (i * 0.8), 1)
                
                formatted_problem = {
                    "id": problem_id,
                    "problem_id": problem_id,
                    "type": "cached_problem",
                    "subject": request.subject,
                    "skill_id": "",
                    "subskill_id": "",
                    "difficulty": difficulty,
                    "timestamp": timestamp,
                    "problem_data": {
                        "problem_type": problem.get("problem_type", "Problem Solving"),
                        "problem": problem.get("problem", ""),
                        "answer": problem.get("answer", ""),
                        "success_criteria": problem.get("success_criteria", []),
                        "teaching_note": problem.get("teaching_note", ""),
                        "grade_level": grade_info,  # Add grade level
                        "metadata": {
                            "subject": request.subject,
                            "grade_level": grade_info,  # Add grade level to metadata
                            "unit": {
                                "id": f"{request.unit.upper().replace(' ', '')}001",
                                "title": request.unit
                            },
                            "skill": {
                                "id": f"{request.unit.upper().replace(' ', '')}001-01",
                                "description": request.skill
                            },
                            "subskill": {
                                "id": f"{request.unit.upper().replace(' ', '')}001-01-{chr(65+i)}",
                                "description": request.subskill
                            },
                            "difficulty": difficulty,
                            "objectives": {
                                "ConceptGroup": "Educational Content Integration",
                                "DetailedObjective": f"Apply understanding of {request.subskill} through multi-modal learning at {grade_info} level",
                                "SubskillDescription": request.subskill
                            }
                        },
                        "problem_id": problem_id,
                        "id": problem_id
                    }
                }
                
                formatted_problems.append(formatted_problem)
            
            return ContentComponent(
                package_id=package_id,
                component_type=ComponentType.PRACTICE,
                content={
                    "problems": formatted_problems,
                    "problem_count": len(formatted_problems),
                    "estimated_time_minutes": len(formatted_problems) * 2,
                    "grade_level": grade_info
                },
                metadata={
                    "problem_count": len(formatted_problems),
                    "estimated_time": len(formatted_problems) * 2,
                    "format": "structured_problems",
                    "grade_level": grade_info
                }
            )
            
        except Exception as e:
            self._handle_generation_error("Practice problems generation", e)

    async def revise_practice_problems(
        self,
        original_content: Dict[str, Any],
        feedback: str,
        master_context: MasterContext
    ) -> Dict[str, Any]:
        """Revise practice problems based on feedback"""
        
        prompt = f"""
        Revise these practice problems based on the feedback provided.

        ORIGINAL PROBLEMS: {json.dumps(original_content, indent=2)}

        FEEDBACK TO ADDRESS: {feedback}

        REQUIREMENTS (maintain coherence):
        - Test the same key terminology: {', '.join(master_context.key_terminology.keys())}
        - Address the same learning objectives: {', '.join(master_context.learning_objectives)}
        - Maintain the same problem format and structure
        - Keep similar difficulty progression
        - Maintain problem count (around {original_content.get('problem_count', 8-10)} problems)
        
        Apply the feedback while maintaining the same educational purpose and format.
        Return the revised problems in the EXACT same JSON format as the original.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.5,
                    max_output_tokens=16000
                )
            )
            
            revised_content = self._safe_json_loads(response.text, "Practice problems revision")
            logger.info("Practice problems revised successfully")
            return revised_content
            
        except Exception as e:
            self._handle_generation_error("Practice problems revision", e)