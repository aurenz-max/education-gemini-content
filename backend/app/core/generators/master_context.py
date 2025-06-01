# backend/app/core/generators/master_context.py
import json
import logging
from google.genai.types import GenerateContentConfig

from .base_generator import BaseContentGenerator
from app.models.content import ContentGenerationRequest, MasterContext
from app.core.schemas import MASTER_CONTEXT_SCHEMA

logger = logging.getLogger(__name__)


class MasterContextGenerator(BaseContentGenerator):
    """Generator for master context that provides foundation for all content"""
    
    async def generate_master_context(self, request: ContentGenerationRequest) -> MasterContext:
        """Generate foundational context for all content - UPDATED WITH GRADE"""
        
        # Get grade information if available from request
        grade_info = self._extract_grade_info(request)
        
        prompt = f"""
        Create a comprehensive educational foundation for teaching this topic:

        Subject: {request.subject}
        Grade Level: {grade_info}
        Unit: {request.unit}
        Skill: {request.skill}
        Subskill: {request.subskill}
        Difficulty: {request.difficulty_level}
        Prerequisites: {', '.join(request.prerequisites) if request.prerequisites else 'None'}

        Requirements for {grade_info} students:
        - 4-6 core concepts appropriate for {grade_info} cognitive development
        - 5-8 key terms with definitions suitable for {grade_info} vocabulary level
        - 4-6 specific, measurable learning objectives aligned with {grade_info} standards
        - 3-5 real-world applications that {grade_info} students can relate to
        - Language complexity and examples appropriate for {grade_info}

        This will be the foundation for generating reading content, visual demos, audio dialogue, and practice problems.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=MASTER_CONTEXT_SCHEMA,
                    temperature=0.3,
                    max_output_tokens=25000
                )
            )
            
            context_data = self._safe_json_loads(response.text, "Master context generation")
            
            # Convert array of term-definition objects back to dictionary
            key_terminology_dict = {}
            if 'key_terminology' in context_data:
                for term_obj in context_data['key_terminology']:
                    if 'term' in term_obj and 'definition' in term_obj:
                        key_terminology_dict[term_obj['term']] = term_obj['definition']
            
            return MasterContext(
                core_concepts=context_data['core_concepts'],
                key_terminology=key_terminology_dict,  # Convert back to dict
                learning_objectives=context_data['learning_objectives'],
                difficulty_level=context_data.get('difficulty_level', request.difficulty_level),
                prerequisites=context_data.get('prerequisites', request.prerequisites),
                real_world_applications=context_data['real_world_applications']
            )
            
        except Exception as e:
            self._handle_generation_error("Master context generation", e)