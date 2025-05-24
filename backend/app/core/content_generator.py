# backend/app/core/content_generator.py
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from google import genai

from google.genai import types

from google.genai.types import (
    GenerateContentConfig,
    SpeechConfig,
    MultiSpeakerVoiceConfig,
    SpeakerVoiceConfig,
    VoiceConfig,
    PrebuiltVoiceConfig,
    Content,
    Part
)

from app.models.content import (
    ContentGenerationRequest, 
    MasterContext, 
    ContentComponent, 
    ComponentType,
    ContentPackage,
    GenerationMetadata
)

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """Core service for generating educational content"""
    
    def __init__(self):
        self.client = None
        self.types = types
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini client"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialized successfully")
    
    async def generate_content_package(self, request: ContentGenerationRequest) -> ContentPackage:
        """Generate complete educational content package"""
        
        start_time = datetime.now()
        package_id = f"pkg_{int(start_time.timestamp())}"
        
        try:
            logger.info(f"Starting content generation for {request.subject}/{request.skill}")
            
            # Stage 1: Generate Master Context
            master_context = await self._generate_master_context(request)
            
            # Stage 2: Generate content components in parallel (where possible)
            reading_task = self._generate_reading_content(request, master_context, package_id)
            visual_task = self._generate_visual_demo(request, master_context, package_id)
            audio_script_task = self._generate_audio_script(request, master_context)
            
            # Wait for parallel tasks
            reading_comp, visual_comp, audio_script = await asyncio.gather(
                reading_task, visual_task, audio_script_task
            )
            
            # Stage 3: Sequential tasks that depend on others
            # Convert audio script to WAV
            audio_comp = await self._generate_audio_from_script(audio_script, package_id)
            
            # Generate practice problems (can use context from reading/visual)
            practice_comp = await self._generate_practice_problems(
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
                    coherence_score=0.90  # Built-in coherence via shared context
                )
            )
            
            logger.info(f"Content generation completed in {generation_time}ms")
            return package
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise
    
    async def _generate_master_context(self, request: ContentGenerationRequest) -> MasterContext:
        """Generate foundational context for all content"""
        
        prompt = f"""
        Create a comprehensive educational foundation for teaching this topic:

        Subject: {request.subject}
        Unit: {request.unit}
        Skill: {request.skill}
        Subskill: {request.subskill}
        Difficulty: {request.difficulty_level}
        Prerequisites: {', '.join(request.prerequisites) if request.prerequisites else 'None'}

        Return a JSON object with these exact fields:
        {{
            "core_concepts": ["concept1", "concept2", "concept3", "concept4"],
            "key_terminology": {{"term1": "definition1", "term2": "definition2"}},
            "learning_objectives": ["objective1", "objective2", "objective3"],
            "difficulty_level": "{request.difficulty_level}",
            "prerequisites": {json.dumps(request.prerequisites)},
            "real_world_applications": ["application1", "application2", "application3"]
        }}

        Requirements:
        - 4-6 core concepts that students must understand
        - 5-8 key terms with precise, student-friendly definitions  
        - 4-6 specific, measurable learning objectives
        - 3-5 real-world applications where this knowledge is used

        This will be the foundation for generating reading content, visual demos, audio dialogue, and practice problems.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.3,
                    max_output_tokens=8096
                )
            )
            
            context_data = json.loads(response.text)
            
            return MasterContext(
                core_concepts=context_data['core_concepts'],
                key_terminology=context_data['key_terminology'],
                learning_objectives=context_data['learning_objectives'],
                difficulty_level=context_data.get('difficulty_level', request.difficulty_level),
                prerequisites=context_data.get('prerequisites', request.prerequisites),
                real_world_applications=context_data['real_world_applications']
            )
            
        except Exception as e:
            logger.error(f"Master context generation failed: {str(e)}")
            raise
    
    async def _generate_reading_content(
        self, request: ContentGenerationRequest, master_context: MasterContext, package_id: str
    ) -> ContentComponent:
        """Generate structured reading content"""
        
        terminology_str = "\n".join([f"- {term}: {defn}" for term, defn in master_context.key_terminology.items()])
        
        prompt = f"""
        Create comprehensive reading content for students learning {request.subskill}.

        Use this EXACT master context:
        Core Concepts: {', '.join(master_context.core_concepts)}
        
        Key Terminology (use these exact definitions):
        {terminology_str}
        
        Learning Objectives: {', '.join(master_context.learning_objectives)}
        
        Real-world Applications: {', '.join(master_context.real_world_applications)}

        Create educational reading content that:
        1. Uses ONLY the terminology defined above
        2. Explains ALL core concepts systematically  
        3. Addresses ALL learning objectives
        4. Includes the real-world applications
        5. Is appropriate for {master_context.difficulty_level} level
        6. Has clear section headings and logical flow

        Return JSON:
        {{
            "title": "Title for the reading content",
            "sections": [
                {{
                    "heading": "Section heading",
                    "content": "Section content text...",
                    "key_terms_used": ["term1", "term2"],
                    "concepts_covered": ["concept1", "concept2"]
                }}
            ],
            "word_count": estimated_word_count,
            "reading_level": "appropriate_grade_level"
        }}

        Target: 800-1200 words of educational content.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.4,
                    max_output_tokens=8096
                )
            )
            
            content_data = json.loads(response.text)
            
            return ContentComponent(
                package_id=package_id,
                component_type=ComponentType.READING,
                content=content_data,
                metadata={
                    "word_count": content_data.get('word_count', 0),
                    "reading_level": content_data.get('reading_level', 'unknown'),
                    "section_count": len(content_data.get('sections', []))
                }
            )
            
        except Exception as e:
            logger.error(f"Reading content generation failed: {str(e)}")
            raise
    
    async def _generate_visual_demo(
        self, request: ContentGenerationRequest, master_context: MasterContext, package_id: str
    ) -> ContentComponent:
        """Generate p5.js interactive demonstration"""
        
        prompt = f"""
        Create an interactive p5.js visualization for {request.subskill}.

        Master Context to demonstrate:
        Core Concepts: {', '.join(master_context.core_concepts)}
        Key Terms: {', '.join(master_context.key_terminology.keys())}
        Learning Objectives: {', '.join(master_context.learning_objectives)}

        Create a complete p5.js program that:
        1. Visually demonstrates the core concepts
        2. Has interactive elements (sliders, buttons, mouse interaction)
        3. Shows real-time changes when parameters are adjusted
        4. Uses clear labels and annotations
        5. Runs without external dependencies

        Return JSON:
        {{
            "p5_code": "complete runnable p5.js code",
            "description": "what the visualization demonstrates",
            "interactive_elements": ["element1", "element2"],
            "concepts_demonstrated": ["concept1", "concept2"],
            "user_instructions": "how students should interact with the demo"
        }}

        The code must be complete and runnable in a web browser with just p5.js loaded.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.5,
                    max_output_tokens=16384
                )
            )
            
            demo_data = json.loads(response.text)
            
            return ContentComponent(
                package_id=package_id,
                component_type=ComponentType.VISUAL,
                content=demo_data,
                metadata={
                    "code_lines": len(demo_data.get('p5_code', '').split('\n')),
                    "interactive": len(demo_data.get('interactive_elements', [])) > 0
                }
            )
            
        except Exception as e:
            logger.error(f"Visual demo generation failed: {str(e)}")
            raise
    
    async def _generate_audio_script(
        self, request: ContentGenerationRequest, master_context: MasterContext
    ) -> str:
        """Generate dialogue script for audio content"""
        
        terminology_str = "\n".join([f"- {term}: {defn}" for term, defn in master_context.key_terminology.items()])
        
        prompt = f"""
        Create a natural educational conversation between a teacher and student about {request.subskill}.

        Master Context to cover:
        Key Terminology: {terminology_str}
        Core Concepts: {', '.join(master_context.core_concepts)}
        Learning Objectives: {', '.join(master_context.learning_objectives)}
        Real-world Applications: {', '.join(master_context.real_world_applications)}

        Create a dialogue that:
        1. Uses ALL key terminology with exact definitions
        2. Explains ALL core concepts through conversation
        3. Student asks realistic questions showing learning progression
        4. Teacher guides discovery, doesn't just lecture
        5. Includes real-world examples
        6. Flows naturally (450-750 words when spoken)

        Format as a clean script:
        Teacher: [what teacher says]
        Student: [what student says]

        Make it feel like a real conversation where the student gradually understands the concepts. 
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    temperature=0.6,
                    max_output_tokens=16384
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Audio script generation failed: {str(e)}")
            raise
    
    async def _generate_audio_from_script(self, script: str, package_id: str) -> ContentComponent:
        """Convert script to audio using Gemini TTS - STRICT VERSION THAT FAILS FAST"""
        
        # Create audio directory if needed
        audio_dir = Path("generated_audio")
        audio_dir.mkdir(exist_ok=True)
        
        logger.info(f"=== AUDIO GENERATION START ===")
        logger.info(f"Package ID: {package_id}")
        logger.info(f"Script length: {len(script)} characters")
        logger.info(f"Script preview: {script[:200]}...")
        
        try:
            logger.info("Calling Gemini TTS API...")
            
            # Generate audio using the corrected API syntax from Google AI Studio reference
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=script,
                config=GenerateContentConfig(  # Direct import
                    response_modalities=["AUDIO"],
                    speech_config=SpeechConfig(  # Direct import
                        multi_speaker_voice_config=MultiSpeakerVoiceConfig(  # Direct import
                            speaker_voice_configs=[
                                SpeakerVoiceConfig(  # Direct import
                                    speaker="Teacher",
                                    voice_config=VoiceConfig(  # Direct import
                                        prebuilt_voice_config=PrebuiltVoiceConfig(  # Direct import
                                            voice_name="Zephyr"
                                        )
                                    )
                                ),
                                SpeakerVoiceConfig(  # Direct import
                                    speaker="Student",
                                    voice_config=VoiceConfig(  # Direct import
                                        prebuilt_voice_config=PrebuiltVoiceConfig(  # Direct import
                                            voice_name="Puck"
                                        )
                                    )
                                )
                            ]
                        )
                    ),
                    temperature=0.3
                )
            )
            
            logger.info("TTS API call completed successfully")
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response has candidates: {hasattr(response, 'candidates')}")
            
            if hasattr(response, 'candidates'):
                logger.info(f"Number of candidates: {len(response.candidates) if response.candidates else 0}")
                
                if response.candidates:
                    candidate = response.candidates[0]
                    logger.info(f"First candidate has content: {hasattr(candidate, 'content') and candidate.content is not None}")
                    
                    if hasattr(candidate, 'content') and candidate.content:
                        logger.info(f"Content has parts: {hasattr(candidate.content, 'parts') and candidate.content.parts is not None}")
                        
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            logger.info(f"Number of parts: {len(candidate.content.parts)}")
                            
                            for i, part in enumerate(candidate.content.parts):
                                logger.info(f"Part {i} has inline_data: {hasattr(part, 'inline_data') and part.inline_data is not None}")
            
            # Extract audio data from response - STRICT VERSION
            audio_data = bytearray()
            
            if not (hasattr(response, 'candidates') and response.candidates):
                raise ValueError("TTS response has no candidates")
            
            candidate = response.candidates[0]
            if not (hasattr(candidate, 'content') and candidate.content):
                raise ValueError("TTS response candidate has no content")
            
            if not (hasattr(candidate.content, 'parts') and candidate.content.parts):
                raise ValueError("TTS response content has no parts")
            
            parts_with_audio = 0
            for part in candidate.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    audio_data.extend(part.inline_data.data)
                    parts_with_audio += 1
                    logger.info(f"Extracted {len(part.inline_data.data)} bytes from part")
            
            logger.info(f"Total parts with audio data: {parts_with_audio}")
            logger.info(f"Total audio data extracted: {len(audio_data)} bytes")
            
            if len(audio_data) == 0:
                raise ValueError("No audio data found in TTS response - all parts were empty")
            
            # Save audio file
            audio_filename = f"audio_{package_id}.wav"
            audio_path = audio_dir / audio_filename
            
            logger.info(f"Saving audio to: {audio_path}")
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            # Verify file was written
            if not audio_path.exists():
                raise ValueError(f"Audio file was not created: {audio_path}")
            
            file_size = audio_path.stat().st_size
            if file_size == 0:
                raise ValueError(f"Audio file is empty: {audio_path}")
            
            logger.info(f"Audio file saved successfully: {file_size} bytes")
            
            # Calculate estimated duration
            word_count = len(script.split())
            estimated_duration = (word_count / 150) * 60  # 150 words per minute
            
            logger.info(f"=== AUDIO GENERATION SUCCESS ===")
            
            return ContentComponent(
                package_id=package_id,
                component_type=ComponentType.AUDIO,
                content={
                    "audio_file_path": str(audio_path),
                    "audio_filename": audio_filename,
                    "dialogue_script": script,
                    "duration_seconds": estimated_duration,
                    "voice_config": {
                        "teacher_voice": "Zephyr",
                        "student_voice": "Puck"
                    },
                    "tts_status": "success"
                },
                metadata={
                    "duration_seconds": estimated_duration,
                    "file_size_bytes": len(audio_data),
                    "script_word_count": word_count,
                    "audio_format": "wav",
                    "tts_success": True
                }
            )
            
        except Exception as e:
            logger.error(f"=== AUDIO GENERATION FAILED ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error(f"Full error details:", exc_info=True)
            
            # FAIL FAST - NO FALLBACKS
            raise RuntimeError(f"Audio generation failed for package {package_id}: {str(e)}") from e
    
    async def _generate_practice_problems(
        self, 
        request: ContentGenerationRequest,
        master_context: MasterContext,
        reading_comp: ContentComponent,
        visual_comp: ContentComponent,
        package_id: str
    ) -> ContentComponent:
        """Generate practice problems integrating all content"""
        
        reading_concepts = [concept for section in reading_comp.content.get('sections', []) 
                          for concept in section.get('concepts_covered', [])]
        visual_elements = visual_comp.content.get('interactive_elements', [])
        
        prompt = f"""
        Create practice problems for {request.subskill} that integrate multiple learning modes.

        Master Context:
        Key Terms: {', '.join(master_context.key_terminology.keys())}
        Learning Objectives: {', '.join(master_context.learning_objectives)}

        Content Integration:
        Reading covered: {', '.join(reading_concepts)}
        Visual demo includes: {', '.join(visual_elements)}

        Generate 8-10 problems that:
        1. Test understanding of key terms
        2. Reference the visual demonstration 
        3. Progress from basic to applied difficulty
        4. Include real-world applications
        5. Require integrated understanding

        For each problem, provide:
        - problem_type: (e.g., "Multiple Choice", "Problem Solving", "Error Detection", "Application")
        - problem: The actual question/problem statement
        - answer: The correct answer or solution
        - success_criteria: Array of 2-3 criteria that define successful completion
        - teaching_note: Helpful note for educators about teaching this concept

        Return JSON with an array of problems in this format:
        {{
            "problems": [
                {{
                    "problem_type": "Multiple Choice",
                    "problem": "What is the slope of the line y = 3x + 5?",
                    "answer": "3",
                    "success_criteria": [
                        "Student identifies slope coefficient in slope-intercept form",
                        "Student distinguishes between slope and y-intercept",
                        "Student demonstrates understanding of linear equation structure"
                    ],
                    "teaching_note": "Emphasize that in y = mx + b form, m is always the slope coefficient."
                }}
            ]
        }}
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.5,
                    max_output_tokens=8096
                )
            )
            
            problems_data = json.loads(response.text)
            
            # Convert to your required format
            formatted_problems = []
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            
            for i, problem in enumerate(problems_data.get('problems', [])):
                problem_uuid = __import__('uuid').uuid4()
                
                # Create problem ID in your format
                problem_id = f"{request.subject}_SKILL-{i+1:02d}_SUBSKILL-{i+1:02d}-A_{timestamp}_{problem_uuid}"
                
                # Calculate difficulty (scale 1-10, varying by problem position)
                difficulty = round(3.0 + (i * 0.8), 1)  # Gradually increasing difficulty
                
                formatted_problem = {
                    "id": problem_id,
                    "problem_id": problem_id,
                    "type": "cached_problem",
                    "subject": request.subject,
                    "skill_id": "",  # Keep empty as requested
                    "subskill_id": "",  # Keep empty as requested
                    "difficulty": difficulty,
                    "timestamp": timestamp,
                    "problem_data": {
                        "problem_type": problem.get("problem_type", "Problem Solving"),
                        "problem": problem.get("problem", ""),
                        "answer": problem.get("answer", ""),
                        "success_criteria": problem.get("success_criteria", []),
                        "teaching_note": problem.get("teaching_note", ""),
                        "metadata": {
                            "subject": request.subject,
                            "unit": {
                                "id": f"{request.unit.upper().replace(' ', '')}001",
                                "title": request.unit
                            },
                            "skill": {
                                "id": f"{request.unit.upper().replace(' ', '')}001-01",
                                "description": request.skill
                            },
                            "subskill": {
                                "id": f"{request.unit.upper().replace(' ', '')}001-01-{chr(65+i)}",  # A, B, C, etc.
                                "description": request.subskill
                            },
                            "difficulty": difficulty,
                            "objectives": {
                                "ConceptGroup": "Educational Content Integration",
                                "DetailedObjective": f"Apply understanding of {request.subskill} through multi-modal learning",
                                "SubskillDescription": request.subskill
                            }
                        },
                        "problem_id": problem_id,
                        "id": problem_id
                    }
                }
                
                formatted_problems.append(formatted_problem)
            
            # Return as ContentComponent with your structure
            return ContentComponent(
                package_id=package_id,
                component_type=ComponentType.PRACTICE,
                content={
                    "problems": formatted_problems,
                    "problem_count": len(formatted_problems),
                    "estimated_time_minutes": len(formatted_problems) * 2  # ~2 minutes per problem
                },
                metadata={
                    "problem_count": len(formatted_problems),
                    "estimated_time": len(formatted_problems) * 2,
                    "format": "structured_problems"
                }
            )
            
        except Exception as e:
            logger.error(f"Practice problems generation failed: {str(e)}")
            raise