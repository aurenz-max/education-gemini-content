# backend/app/core/generators/reading_content.py
import json
import logging
from typing import Dict, Any
from google.genai.types import GenerateContentConfig

from .base_generator import BaseContentGenerator
from app.models.content import ContentGenerationRequest, MasterContext, ContentComponent, ComponentType
from app.core.schemas import READING_CONTENT_SCHEMA

logger = logging.getLogger(__name__)


class ReadingContentGenerator(BaseContentGenerator):
    """Generator for structured reading content"""
    
    async def generate_reading_content(
        self, request: ContentGenerationRequest, master_context: MasterContext, package_id: str
    ) -> ContentComponent:
        """Generate structured reading content - UPDATED WITH GRADE"""
        
        terminology_str = self._format_terminology_string(master_context.key_terminology)
        grade_info = self._extract_grade_info(request)
        
        prompt = f"""
        Create comprehensive reading content for {grade_info} students learning {request.subskill}.

        Target Audience: {grade_info} students
        Subject: {request.subject}
        
        Use this EXACT master context:
        Core Concepts: {', '.join(master_context.core_concepts)}
        
        Key Terminology (use these exact definitions):
        {terminology_str}
        
        Learning Objectives: {', '.join(master_context.learning_objectives)}
        
        Real-world Applications: {', '.join(master_context.real_world_applications)}

        Create educational reading content that:
        1. Uses language appropriate for {grade_info} reading level
        2. Uses ONLY the terminology defined above with age-appropriate explanations
        3. Explains ALL core concepts systematically using examples {grade_info} students understand
        4. Addresses ALL learning objectives
        5. Includes real-world applications relevant to {grade_info} students
        6. Is appropriate for {master_context.difficulty_level} level within {grade_info}
        7. Has clear section headings and logical flow
        8. Uses sentence structure and vocabulary suitable for {grade_info}

        Target: 800-1200 words of educational content appropriate for {grade_info}.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=READING_CONTENT_SCHEMA,
                    temperature=0.4,
                    max_output_tokens=25000
                )
            )
            
            content_data = self._safe_json_loads(response.text, "Reading content generation")
            
            return ContentComponent(
                package_id=package_id,
                component_type=ComponentType.READING,
                content=content_data,
                metadata={
                    "word_count": content_data.get('word_count', 0),
                    "reading_level": content_data.get('reading_level', grade_info),
                    "grade_level": grade_info,
                    "section_count": len(content_data.get('sections', []))
                }
            )
            
        except Exception as e:
            self._handle_generation_error("Reading content generation", e)

    async def revise_reading_content(
        self,
        original_content: Dict[str, Any],
        feedback: str,
        master_context: MasterContext
    ) -> Dict[str, Any]:
        """Revise reading content based on feedback"""
        
        # Use same terminology for coherence
        terminology_str = self._format_terminology_string(master_context.key_terminology)
        
        prompt = f"""
        Revise this educational reading content based on the feedback provided.

        ORIGINAL CONTENT: {json.dumps(original_content, indent=2)}

        FEEDBACK TO ADDRESS: {feedback}

        REQUIREMENTS (maintain coherence):
        - Keep the same key terminology: {terminology_str}
        - Address the same learning objectives: {', '.join(master_context.learning_objectives)}
        - Maintain {master_context.difficulty_level} difficulty level
        - Keep the same overall structure and format
        
        Apply the feedback while maintaining all existing terminology and concepts.
        Return the revised content in the EXACT same JSON format as the original.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.4,
                    max_output_tokens=25000
                )
            )
            
            revised_content = self._safe_json_loads(response.text, "Reading content revision")
            logger.info("Reading content revised successfully")
            return revised_content
            
        except Exception as e:
            self._handle_generation_error("Reading content revision", e)