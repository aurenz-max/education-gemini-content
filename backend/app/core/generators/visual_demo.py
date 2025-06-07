# backend/app/core/generators/visual_demo.py
import json
import logging
from typing import Dict, Any
from google.genai.types import GenerateContentConfig

from .base_generator import BaseContentGenerator
from app.models.content import ContentGenerationRequest, MasterContext, ContentComponent, ComponentType
from app.core.schemas import VISUAL_METADATA_SCHEMA

logger = logging.getLogger(__name__)


class VisualDemoGenerator(BaseContentGenerator):
    """Generator for p5.js interactive demonstrations"""
    
    async def generate_visual_demo(
        self, request: ContentGenerationRequest, master_context: MasterContext, package_id: str
    ) -> ContentComponent:
        """Generate p5.js interactive demonstration - SPLIT INTO TWO FUNCTIONS"""
        
        # Step 1: Generate the p5.js code
        p5_code = await self.generate_p5js_code(request, master_context)
        
        # Step 2: Generate metadata based on the code
        demo_metadata = await self.generate_visual_metadata(p5_code, request, master_context)
        
        # Combine the results
        demo_data = {
            "p5_code": p5_code,
            **demo_metadata
        }
        
        grade_info = self._extract_grade_info(request)
        
        return ContentComponent(
            package_id=package_id,
            component_type=ComponentType.VISUAL,
            content=demo_data,
            metadata={
                "code_lines": len(p5_code.split('\n')),
                "interactive": len(demo_data.get('interactive_elements', [])) > 0,
                "grade_level": grade_info,
                "age_appropriate": True,
                "concepts_count": len(demo_data.get('concepts_demonstrated', [])),
                "educational_focus": "master_context_concepts",
                "has_canvas_resize": True,
                "engagement_level": "high_interactivity"
            }
        )

    async def generate_p5js_code(
        self, request: ContentGenerationRequest, master_context: MasterContext
    ) -> str:
        """Generate only the p5.js code"""
        
        grade_info = self._extract_grade_info(request)
        
        prompt = f"""
        Create an educational interactive p5.js script that teaches the following skill:
        Main Skill: {request.skill}
        Subskill: {request.subskill}
        Target Age Level: {grade_info}
        Difficulty Level: {master_context.difficulty_level}
        Subject: {request.subject}

        Master Context to demonstrate:
        Core Concepts: {', '.join(master_context.core_concepts)}
        Key Terms: {', '.join(master_context.key_terminology.keys())}
        Key Terminology: {', '.join([f"{term}: {defn}" for term, defn in master_context.key_terminology.items()])}
        Learning Objectives: {', '.join(master_context.learning_objectives)}
        Real-world Applications: {', '.join(master_context.real_world_applications)}

        Your p5.js script must:
        1. Be complete and executable in a standard p5.js environment
        2. Include setup() and draw() functions
        3. Have comprehensive comments explaining the educational concepts from the master context
        4. Be highly engaging and interactive for {grade_info}:
            a. Prioritize intuitive mouse/touch/keyboard interactions appropriate for {grade_info} motor skills
            b. Provide clear visual feedback for user actions that {grade_info} students can understand
            c. Use appealing visuals (colors, shapes, simple animations) appropriate for {grade_info}
            d. Aim for a "discovery" or "aha!" moment that demonstrates the core concepts
        5. Encourage experimentation and creative exploration suitable for {grade_info} cognitive level
        6. Include student interaction to reinforce the learning objectives
        7. Follow coding best practices with well-organized structure
        8. Include a title and brief description at the top explaining what {grade_info} students will learn
        9. Include Canvas Resize to fit the browser's window
        10. Visually demonstrate the core concepts in a way {grade_info} students can understand
        11. Use colors, shapes, and animations that engage {grade_info} students
        12. Show real-time changes when parameters are adjusted
        13. Use clear, large labels and annotations readable by {grade_info} students
        14. Include instructions simple enough for {grade_info} to follow independently

        Age-appropriate considerations for {grade_info}:
        - Use bright, engaging colors
        - Keep interactions simple and intuitive
        - Provide immediate visual feedback
        - Include encouraging text/messages
        - Make clickable areas large enough for young fingers (if applicable)
        - Use vocabulary and concepts appropriate for {grade_info}

        The exhibit should be educational but engaging, allowing students to manipulate parameters and see the results in real-time while learning the core concepts.

        Return ONLY the complete p5.js code without any JSON formatting or additional text. The code should be ready to run directly in a p5.js environment.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-pro-preview-06-05',
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=25000
                )
            )
            
            p5_code = response.text.strip()
            
            # Clean up any potential markdown formatting
            if p5_code.startswith("```javascript"):
                p5_code = p5_code.replace("```javascript", "").replace("```", "").strip()
            elif p5_code.startswith("```"):
                p5_code = p5_code.replace("```", "").strip()
            
            logger.info("P5.js code generated successfully")
            return p5_code
            
        except Exception as e:
            self._handle_generation_error("P5.js code generation", e)

    async def generate_visual_metadata(
        self, p5_code: str, request: ContentGenerationRequest, master_context: MasterContext
    ) -> Dict[str, Any]:
        """Generate metadata for the visual demo based on the p5.js code - IMPROVED ERROR HANDLING"""
        
        grade_info = self._extract_grade_info(request)
        
        # Limit the p5_code length to avoid token limit issues
        code_preview = p5_code[:2000] + "..." if len(p5_code) > 2000 else p5_code
        
        prompt = f"""
        Analyze this p5.js code and describe its educational features for {grade_info} students learning {request.subskill}.

        P5.JS CODE TO ANALYZE (first 2000 characters):
        {code_preview}

        MASTER CONTEXT FOR REFERENCE:
        Core Concepts: {', '.join(master_context.core_concepts)}
        Key Terms: {', '.join(master_context.key_terminology.keys())}
        Learning Objectives: {', '.join(master_context.learning_objectives)}
        Real-world Applications: {', '.join(master_context.real_world_applications)}

        Provide concise but complete information about:
        1. What the visualization demonstrates (max 200 words)
        2. Specific interactive elements that students can use
        3. Which core concepts from the master context are demonstrated
        4. Step-by-step instructions for {grade_info} students (be concise)
        5. Features that make it appropriate and engaging for {grade_info}
        6. How it addresses each learning objective
        7. The educational value for reinforcing key terminology and concepts

        Keep descriptions clear and concise. Avoid unnecessary detail.
        Focus on the actual functionality present in the code and how it serves the educational goals for {grade_info} students.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=VISUAL_METADATA_SCHEMA,
                    temperature=0.4,
                    max_output_tokens=15000  # Reduced from 15000 to avoid truncation
                )
            )
            
            # Enhanced JSON parsing with better error handling
            response_text = response.text.strip()
            logger.info(f"Visual metadata response length: {len(response_text)} characters")
            
            # Check if response appears truncated
            if response_text and not response_text.endswith('}'):
                logger.warning("Visual metadata response appears truncated - attempting to fix")
                # Try to close any open JSON structures
                if response_text.count('{') > response_text.count('}'):
                    response_text += '"}'  # Close any open string and object
                elif response_text.count('[') > response_text.count(']'):
                    response_text += '"]}'  # Close any open array and object
            
            try:
                metadata = self._safe_json_loads(response_text, "Visual demo metadata generation")
            except ValueError as json_error:
                # If JSON parsing fails, create a fallback response
                logger.warning(f"JSON parsing failed, creating fallback metadata: {json_error}")
                metadata = self._create_fallback_visual_metadata(request, master_context)
            
            logger.info("Visual demo metadata generated successfully")
            return metadata
            
        except Exception as e:
            logger.warning(f"Visual metadata generation failed: {e}, creating fallback")
            # Return fallback metadata instead of failing completely
            return self._create_fallback_visual_metadata(request, master_context)

    def _create_fallback_visual_metadata(
        self, request: ContentGenerationRequest, master_context: MasterContext
    ) -> Dict[str, Any]:
        """Create fallback metadata when generation fails"""
        grade_info = self._extract_grade_info(request)
        
        return {
            "description": f"Interactive visualization for {grade_info} students learning {request.subskill}. The demo uses visual elements to demonstrate core concepts and allows students to interact with the material.",
            "interactive_elements": [
                "Mouse click interactions",
                "Visual feedback",
                "Real-time updates",
                "Clear labels and instructions"
            ],
            "concepts_demonstrated": master_context.core_concepts[:3],  # Take first 3
            "user_instructions": f"Click and interact with the visual elements to explore {request.subskill}. Watch how the display changes as you interact with different parts of the demo.",
            "grade_appropriate_features": [
                f"Age-appropriate visuals for {grade_info}",
                "Clear, simple instructions",
                "Immediate visual feedback",
                "Engaging colors and animations"
            ],
            "learning_objectives_addressed": master_context.learning_objectives[:3],  # Take first 3
            "educational_value": f"This demo helps {grade_info} students understand {request.subskill} through visual and interactive learning, reinforcing key concepts through hands-on exploration."
        }

    async def revise_visual_demo(
        self,
        original_content: Dict[str, Any],
        feedback: str,
        master_context: MasterContext
    ) -> Dict[str, Any]:
        """Revise visual demo based on feedback"""
        
        prompt = f"""
        Revise this p5.js interactive demonstration based on the feedback provided.

        ORIGINAL DEMO: {json.dumps(original_content, indent=2)}

        FEEDBACK TO ADDRESS: {feedback}

        REQUIREMENTS (maintain coherence):
        - Demonstrate the same core concepts: {', '.join(master_context.core_concepts)}
        - Use the same key terminology: {', '.join(master_context.key_terminology.keys())}
        - Keep the same educational objectives
        - Maintain interactive elements where possible
        
        Apply the feedback while keeping the same educational purpose.
        Return the revised demo in the EXACT same JSON format as the original.
        The p5.js code must be complete and runnable.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-pro-preview-06-05',
                contents=prompt,
                config=GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.5,
                    max_output_tokens=25000
                )
            )
            
            revised_content = self._safe_json_loads(response.text, "Visual demo revision")
            logger.info("Visual demo revised successfully")
            return revised_content
            
        except Exception as e:
            self._handle_generation_error("Visual demo revision", e)