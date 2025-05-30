# backend/app/core/content_generator.py
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List



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
    GenerationMetadata,
    ComponentRevision, 
    RevisionEntry, 
)

# Import your existing services
from app.database.cosmos_client import cosmos_service
from app.database.blob_storage import blob_storage_service
from app.config import settings

logger = logging.getLogger(__name__)

logging.getLogger('azure').setLevel(logging.WARNING)  # or logging.ERROR for even less output
logging.getLogger('azure.cosmos').setLevel(logging.INFO)  # Specifically for Cosmos DB
logging.getLogger('urllib3').setLevel(logging.WARNING)  # For HTTP request logs


class ContentGenerationService:
    """Core service for generating educational content"""
    
    def __init__(self):
        self.client = None
        self.types = types
        self.cosmos_service = cosmos_service
        self.blob_service = blob_storage_service
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini client with configuration"""
        if not settings.GEMINI_API_KEY:
            raise ValueError(f"GEMINI_API_KEY is required. Please check your configuration in {settings.ENVIRONMENT} mode.")
        
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Gemini client initialized successfully (Environment: {settings.ENVIRONMENT})")
    
    async def generate_content_package(self, request: ContentGenerationRequest) -> ContentPackage:
        """Generate complete educational content package and store it"""
        
        start_time = datetime.now()
        package_id = f"pkg_{int(start_time.timestamp())}"
        
        try:
            logger.info(f"Starting content generation for {request.subject}/{request.skill}")
            
            # Generate master context with grade information
            master_context = await self._generate_master_context(request)
            
            reading_task = self._generate_reading_content(request, master_context, package_id)
            visual_task = self._generate_visual_demo(request, master_context, package_id)
            audio_script_task = self._generate_audio_script(request, master_context)
            
            reading_comp, visual_comp, audio_script = await asyncio.gather(
                reading_task, visual_task, audio_script_task
            )
            
            # Generate audio and upload to blob storage
            audio_comp = await self._generate_and_store_audio(audio_script, package_id)
            
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
                    coherence_score=0.90
                )
            )
            
            # Store in Cosmos DB
            stored_package = await self.cosmos_service.create_content_package(package)
            
            logger.info(f"Content generation and storage completed in {generation_time}ms")
            return stored_package
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            await self._cleanup_on_failure(package_id)
            raise

    async def _generate_master_context(self, request: ContentGenerationRequest) -> MasterContext:
        """Generate foundational context for all content - UPDATED WITH GRADE"""
        
        # Get grade information if available from request
        grade_info = getattr(request, 'grade', None) or "grade level not specified"
        
        prompt = f"""
        Create a comprehensive educational foundation for teaching this topic:

        Subject: {request.subject}
        Grade Level: {grade_info}
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
            "grade_level": "{grade_info}",
            "prerequisites": {json.dumps(request.prerequisites)},
            "real_world_applications": ["application1", "application2", "application3"]
        }}

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
                config=self.types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.3,
                    max_output_tokens=25000
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
        """Generate structured reading content - UPDATED WITH GRADE"""
        
        terminology_str = "\n".join([f"- {term}: {defn}" for term, defn in master_context.key_terminology.items()])
        grade_info = getattr(request, 'grade', None) or "appropriate grade level"
        
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
            "reading_level": "{grade_info}",
            "grade_appropriate_features": ["feature1", "feature2"]
        }}

        Target: 800-1200 words of educational content appropriate for {grade_info}.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.4,
                    max_output_tokens=25000
                )
            )
            
            content_data = json.loads(response.text)
            
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
            logger.error(f"Reading content generation failed: {str(e)}")
            raise

    async def _generate_visual_demo(
        self, request: ContentGenerationRequest, master_context: MasterContext, package_id: str
    ) -> ContentComponent:
        """Generate p5.js interactive demonstration - UPDATED WITH GRADE"""
        
        grade_info = getattr(request, 'grade', None) or "appropriate grade level"
        
        prompt = f"""
        Create an interactive p5.js visualization for {grade_info} students learning {request.subskill}.

        Target Audience: {grade_info} students
        Subject: {request.subject}

        Master Context to demonstrate:
        Core Concepts: {', '.join(master_context.core_concepts)}
        Key Terms: {', '.join(master_context.key_terminology.keys())}
        Learning Objectives: {', '.join(master_context.learning_objectives)}

        Create a complete p5.js program that:
        1. Visually demonstrates the core concepts in a way {grade_info} students can understand
        2. Has interactive elements appropriate for {grade_info} motor skills and cognitive level
        3. Uses colors, shapes, and animations that engage {grade_info} students
        4. Shows real-time changes when parameters are adjusted
        5. Uses clear, large labels and annotations readable by {grade_info} students
        6. Includes instructions simple enough for {grade_info} to follow independently
        7. Runs without external dependencies
        8. Has appropriate complexity for {grade_info} attention span

        Age-appropriate considerations for {grade_info}:
        - Use bright, engaging colors
        - Keep interactions simple and intuitive
        - Provide immediate visual feedback
        - Include encouraging text/messages
        - Make clickable areas large enough for young fingers (if applicable)

        Return JSON:
        {{
            "p5_code": "complete runnable p5.js code",
            "description": "what the visualization demonstrates",
            "interactive_elements": ["element1", "element2"],
            "concepts_demonstrated": ["concept1", "concept2"],
            "user_instructions": "simple instructions for {grade_info} students",
            "grade_appropriate_features": ["feature1", "feature2"]
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
                    max_output_tokens=25000
                )
            )
            
            demo_data = json.loads(response.text)
            
            return ContentComponent(
                package_id=package_id,
                component_type=ComponentType.VISUAL,
                content=demo_data,
                metadata={
                    "code_lines": len(demo_data.get('p5_code', '').split('\n')),
                    "interactive": len(demo_data.get('interactive_elements', [])) > 0,
                    "grade_level": grade_info,
                    "age_appropriate": True
                }
            )
            
        except Exception as e:
            logger.error(f"Visual demo generation failed: {str(e)}")
            raise

    async def _generate_audio_script(
        self, request: ContentGenerationRequest, master_context: MasterContext
    ) -> str:
        """Generate dialogue script for audio content - UPDATED WITH GRADE"""
        
        terminology_str = "\n".join([f"- {term}: {defn}" for term, defn in master_context.key_terminology.items()])
        grade_info = getattr(request, 'grade', None) or "appropriate grade level"
        
        prompt = f"""
        Create a natural educational conversation between a teacher and {grade_info} student about {request.subskill}.

        Target Audience: {grade_info} student
        Subject: {request.subject}

        Master Context to cover:
        Key Terminology: {terminology_str}
        Core Concepts: {', '.join(master_context.core_concepts)}
        Learning Objectives: {', '.join(master_context.learning_objectives)}
        Real-world Applications: {', '.join(master_context.real_world_applications)}

        Create a dialogue that:
        1. Uses language and vocabulary appropriate for {grade_info}
        2. Uses ALL key terminology with explanations suitable for {grade_info}
        3. Explains ALL core concepts through age-appropriate conversation
        4. Student asks realistic questions that {grade_info} students would ask
        5. Teacher uses examples and analogies {grade_info} students can relate to
        6. Teacher guides discovery with patience appropriate for {grade_info}
        7. Includes real-world examples relevant to {grade_info} experience
        8. Flows naturally and maintains {grade_info} attention (450-750 words when spoken)
        9. Uses encouraging, supportive tone appropriate for {grade_info}

        Grade-specific considerations for {grade_info}:
        - Use simple, clear sentence structures
        - Include relatable examples from {grade_info} daily life
        - Teacher shows patience and uses positive reinforcement
        - Student shows curiosity and excitement appropriate for {grade_info}
        - Include "aha!" moments and celebrations of understanding

        Format as a clean script:
        Teacher: [what teacher says]
        Student: [what student says]

        Make it feel like a real conversation where the {grade_info} student gradually understands the concepts with age-appropriate excitement and curiosity.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    temperature=0.6,
                    max_output_tokens=25000
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Audio script generation failed: {str(e)}")
            raise

    async def _generate_practice_problems(
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
        grade_info = getattr(request, 'grade', None) or "appropriate grade level"
        
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

        Return JSON with an array of problems in this format:
        {{
            "problems": [
                {{
                    "problem_type": "Multiple Choice",
                    "problem": "Age-appropriate question for {grade_info}",
                    "answer": "Clear answer",
                    "success_criteria": [
                        "Student shows understanding appropriate for {grade_info}",
                        "Student can explain using {grade_info} vocabulary",
                        "Student demonstrates concept through {grade_info} appropriate method"
                    ],
                    "teaching_note": "Guidance for teaching this to {grade_info} students",
                    "grade_level": "{grade_info}"
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
                    max_output_tokens=16000
                )
            )
            
            problems_data = json.loads(response.text)
            
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
            logger.error(f"Practice problems generation failed: {str(e)}")
            raise

    async def _generate_and_store_audio(self, script: str, package_id: str) -> ContentComponent:
        """Generate audio and upload to blob storage"""
        
        audio_dir = Path("generated_audio")
        audio_dir.mkdir(exist_ok=True)
        
        logger.info(f"Generating audio for package: {package_id}")
        
        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=script,
                config=GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=SpeechConfig(
                        multi_speaker_voice_config=MultiSpeakerVoiceConfig(
                            speaker_voice_configs=[
                                SpeakerVoiceConfig(
                                    speaker="Teacher",
                                    voice_config=VoiceConfig(
                                        prebuilt_voice_config=PrebuiltVoiceConfig(
                                            voice_name="Zephyr"
                                        )
                                    )
                                ),
                                SpeakerVoiceConfig(
                                    speaker="Student",
                                    voice_config=VoiceConfig(
                                        prebuilt_voice_config=PrebuiltVoiceConfig(
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
            
            # Extract audio data
            audio_data = bytearray()
            if not (hasattr(response, 'candidates') and response.candidates):
                raise ValueError("TTS response has no candidates")
            
            candidate = response.candidates[0]
            if not (hasattr(candidate, 'content') and candidate.content):
                raise ValueError("TTS response candidate has no content")
            
            if not (hasattr(candidate.content, 'parts') and candidate.content.parts):
                raise ValueError("TTS response content has no parts")
            
            for part in candidate.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    audio_data.extend(part.inline_data.data)
            
            if len(audio_data) == 0:
                raise ValueError("No audio data found in TTS response")
            
            # Save temporary file
            audio_filename = f"audio_{package_id}.wav"
            temp_audio_path = audio_dir / audio_filename
            
            with open(temp_audio_path, 'wb') as f:
                f.write(audio_data)
            
            # Upload to blob storage
            logger.info(f"Uploading audio to blob storage: {audio_filename}")
            upload_result = await self.blob_service.upload_audio_file(
                package_id=package_id,
                file_path=str(temp_audio_path),
                filename=audio_filename,
                overwrite=True
            )
            
            if not upload_result["success"]:
                raise RuntimeError(f"Failed to upload audio: {upload_result['error']}")
            
            # Calculate duration
            word_count = len(script.split())
            estimated_duration = (word_count / 150) * 60
            
            logger.info(f"Audio uploaded successfully: {upload_result['blob_url']}")
            
            return ContentComponent(
                package_id=package_id,
                component_type=ComponentType.AUDIO,
                content={
                    "audio_blob_url": upload_result["blob_url"],
                    "audio_filename": audio_filename,
                    "dialogue_script": script,
                    "duration_seconds": estimated_duration,
                    "voice_config": {
                        "teacher_voice": "Zephyr",
                        "student_voice": "Puck"
                    },
                    "tts_status": "success",
                    "blob_name": upload_result["blob_name"]
                },
                metadata={
                    "duration_seconds": estimated_duration,
                    "file_size_bytes": len(audio_data),
                    "script_word_count": word_count,
                    "audio_format": "wav",
                    "tts_success": True,
                    "stored_in_blob": True
                }
            )
            
        except Exception as e:
            logger.error(f"Audio generation and storage failed: {str(e)}")
            raise RuntimeError(f"Audio generation failed for package {package_id}: {str(e)}") from e


    async def _cleanup_on_failure(self, package_id: str):
        """Clean up any uploaded files if generation fails"""
        try:
            logger.info(f"Cleaning up failed package: {package_id}")
            cleanup_result = await self.blob_service.cleanup_package_audio(package_id)
            if cleanup_result["success"]:
                logger.info(f"Cleaned up {cleanup_result['deleted_count']} audio files")
            else:
                logger.warning(f"Cleanup had errors: {cleanup_result.get('errors', [])}")
        except Exception as e:
            logger.warning(f"Cleanup failed (non-critical): {str(e)}")

    async def get_content_package(self, package_id: str, subject: str, unit: str) -> ContentPackage:
        """Retrieve a content package from storage"""
        partition_key = f"{subject}-{unit}"
        package = await self.cosmos_service.get_content_package(package_id, partition_key)
        if not package:
            raise ValueError(f"Content package {package_id} not found")
        return package

    async def list_content_packages(self, subject: str = None, unit: str = None) -> list[ContentPackage]:
        """List content packages with optional filtering"""
        return await self.cosmos_service.list_content_packages(
            subject=subject,
            unit=unit,
            limit=100
        )

    async def delete_content_package(self, package_id: str, subject: str, unit: str) -> bool:
        """Delete a content package and clean up associated files"""
        partition_key = f"{subject}-{unit}"
        
        try:
            # Delete from Cosmos DB
            deleted = await self.cosmos_service.delete_content_package(package_id, partition_key)
            if not deleted:
                return False
            
            # Clean up blob storage
            cleanup_result = await self.blob_service.cleanup_package_audio(package_id)
            logger.info(f"Cleaned up {cleanup_result.get('deleted_count', 0)} audio files")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete package {package_id}: {str(e)}")
            return False

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
                    max_output_tokens=25000
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
                    max_output_tokens=25000
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
        """Generate p5.js interactive demonstration - UPDATED WITH GRADE"""
        
        grade_info = getattr(request, 'grade', None) or "appropriate grade level"
        
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

        Return JSON:
        {{
            "p5_code": "/* p5.js Educational Script: {request.skill} */\\n\\n// Complete runnable p5.js code with proper syntax and indentation",
            "description": "Clear description of what the visualization demonstrates and how it teaches the core concepts",
            "interactive_elements": ["specific interactive element 1", "specific interactive element 2"],
            "concepts_demonstrated": ["core concept 1 from master context", "core concept 2 from master context"],
            "user_instructions": "Simple, step-by-step instructions for {grade_info} students on how to interact with the demo",
            "grade_appropriate_features": ["engaging feature 1 for {grade_info}", "engaging feature 2 for {grade_info}"],
            "learning_objectives_addressed": ["how objective 1 is demonstrated", "how objective 2 is demonstrated"],
            "educational_value": "Explanation of how this demo reinforces the key terminology and concepts for {grade_info} students"
        }}

        The code must be complete and runnable in a web browser with just p5.js loaded, formatted as a valid JavaScript file with proper syntax and indentation.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.5,
                    max_output_tokens=25000
                )
            )
            
            demo_data = json.loads(response.text)
            
            return ContentComponent(
                package_id=package_id,
                component_type=ComponentType.VISUAL,
                content=demo_data,
                metadata={
                    "code_lines": len(demo_data.get('p5_code', '').split('\n')),
                    "interactive": len(demo_data.get('interactive_elements', [])) > 0,
                    "grade_level": grade_info,
                    "age_appropriate": True,
                    "concepts_count": len(demo_data.get('concepts_demonstrated', [])),
                    "educational_focus": "master_context_concepts",
                    "has_canvas_resize": True,
                    "engagement_level": "high_interactivity"
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
                    max_output_tokens=25000
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
        package_id: str
    ) -> ContentComponent:
        """Generate practice problems based on master context - UPDATED WITH GRADE"""
        
        grade_info = getattr(request, 'grade', None) or "appropriate grade level"
        
        prompt = f"""
        Create practice problems for {grade_info} students learning {request.subskill}.

        Target Audience: {grade_info} students
        Subject: {request.subject}

        Master Context:
        Key Terms: {', '.join(master_context.key_terminology.keys())}
        Key Terminology Definitions: {', '.join([f"{term}: {defn}" for term, defn in master_context.key_terminology.items()])}
        Core Concepts: {', '.join(master_context.core_concepts)}
        Learning Objectives: {', '.join(master_context.learning_objectives)}
        Real-world Applications: {', '.join(master_context.real_world_applications)}

        Generate 8-10 problems that:
        1. Test understanding of key terms and their definitions at {grade_info} level
        2. Assess comprehension of core concepts using {grade_info} appropriate language
        3. Evaluate achievement of learning objectives through age-appropriate tasks
        4. Apply knowledge to real-world scenarios relevant to {grade_info} students
        5. Progress from basic recall to application difficulty suitable for {grade_info}
        6. Use vocabulary and problem formats familiar to {grade_info} students
        7. Include encouraging, positive language
        8. Have clear, simple instructions appropriate for {grade_info}

        Grade-specific considerations for {grade_info}:
        - Use vocabulary and sentence structures appropriate for {grade_info}
        - Include visual or concrete examples when possible
        - Make instructions clear and step-by-step
        - Use familiar contexts and scenarios
        - Provide positive, encouraging feedback criteria

        For each problem, provide:
        - problem_type: (e.g., "Multiple Choice", "Problem Solving", "Drawing/Visual", "Real-World Application", "Definition Match")
        - problem: The actual question/problem statement (written for {grade_info})
        - answer: The correct answer or solution
        - success_criteria: Array of 2-3 criteria that define successful completion for {grade_info}
        - teaching_note: Helpful note for educators about teaching this concept to {grade_info}

        Return JSON with an array of problems in this format:
        {{
            "problems": [
                {{
                    "problem_type": "Multiple Choice",
                    "problem": "Age-appropriate question for {grade_info}",
                    "answer": "Clear answer",
                    "success_criteria": [
                        "Student shows understanding appropriate for {grade_info}",
                        "Student can explain using {grade_info} vocabulary",
                        "Student demonstrates concept through {grade_info} appropriate method"
                    ],
                    "teaching_note": "Guidance for teaching this to {grade_info} students",
                    "grade_level": "{grade_info}"
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
                    max_output_tokens=16000
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

    async def revise_content_package(
        self, 
        package_id: str, 
        subject: str, 
        unit: str,
        revisions: List[ComponentRevision],
        reviewer_id: str = None
    ) -> ContentPackage:
        """
        Revise specific components of a content package
        
        Args:
            package_id: ID of package to revise  
            subject: Subject for partition key
            unit: Unit for partition key
            revisions: List of component revisions to apply
            reviewer_id: ID of reviewer requesting changes
            
        Returns:
            Updated ContentPackage with revised components
        """
        start_time = datetime.now()
        partition_key = f"{subject}-{unit}"
        
        try:
            logger.info(f"Starting revision for package {package_id}")
            logger.info(f"Components to revise: {[r.component_type.value for r in revisions]}")
            
            # Get existing package
            package = await self.cosmos_service.get_content_package(package_id, partition_key)
            if not package:
                raise ValueError(f"Package {package_id} not found")
            
            # Convert to dict for easier manipulation - use mode='json' to serialize datetime objects
            package_dict = package.model_dump(mode='json')
            
            # Process each revision
            revision_entries = []
            for revision in revisions:
                logger.info(f"Revising {revision.component_type.value} component")
                
                revision_start_time = datetime.now()
                
                # Revise the specific component
                revised_content = await self._revise_component(
                    component_type=revision.component_type,
                    original_content=package_dict["content"][revision.component_type.value],
                    feedback=revision.feedback,
                    master_context=package.master_context,
                    package_id=package_id
                )
                
                # Update the content
                package_dict["content"][revision.component_type.value] = revised_content
                
                # Track revision time
                revision_time = int((datetime.now() - revision_start_time).total_seconds() * 1000)
                
                # Create revision entry with proper datetime handling
                revision_entry = RevisionEntry(
                    component_type=revision.component_type,
                    feedback=revision.feedback,
                    reviewer_id=reviewer_id,
                    generation_time_ms=revision_time
                )
                revision_entries.append(revision_entry)
            
            # Update package metadata
            total_time = int((datetime.now() - start_time).total_seconds() * 1000)
            package_dict["status"] = "needs_review"  # Back to review after revision
            package_dict["updated_at"] = datetime.now().isoformat()  # Convert to string
            
            # Add revision history with proper datetime serialization
            if "revision_history" not in package_dict:
                package_dict["revision_history"] = []
            
            # Add new revision entries with explicit datetime handling
            for entry in revision_entries:
                # Convert the RevisionEntry to dict and ensure datetime serialization
                entry_dict = entry.model_dump()
                
                # Add timestamp if not present
                if "timestamp" not in entry_dict:
                    entry_dict["timestamp"] = datetime.now().isoformat()
                
                # Ensure all datetime fields are strings
                for key, value in entry_dict.items():
                    if isinstance(value, datetime):
                        entry_dict[key] = value.isoformat()
                
                package_dict["revision_history"].append(entry_dict)
            
            # Update generation metadata
            if "generation_metadata" not in package_dict:
                package_dict["generation_metadata"] = {}
            
            # Safely update generation metadata
            current_time = package_dict["generation_metadata"].get("generation_time_ms", 0)
            package_dict["generation_metadata"]["generation_time_ms"] = current_time + total_time
            
            # Ensure all datetime fields in the entire package are serialized
            package_dict = self._serialize_datetime_fields(package_dict)
            
            # Convert back to ContentPackage and update in database
            updated_package = ContentPackage(**package_dict)
            stored_package = await self.cosmos_service.update_content_package(updated_package)
            
            logger.info(f"Package revision completed in {total_time}ms")
            logger.info(f"Revised components: {[r.component_type.value for r in revisions]}")
            
            return stored_package
            
        except Exception as e:
            logger.error(f"Package revision failed: {str(e)}")
            # Clean up any uploaded files on failure (reuse existing cleanup)
            await self._cleanup_on_failure(package_id)
            raise

    async def _revise_component(
        self,
        component_type: ComponentType,
        original_content: Dict[str, Any],
        feedback: str,
        master_context,
        package_id: str
    ) -> Dict[str, Any]:
        """Route revision to appropriate component-specific method"""
        
        if component_type == ComponentType.READING:
            return await self._revise_reading_content(original_content, feedback, master_context)
        elif component_type == ComponentType.VISUAL:
            return await self._revise_visual_demo(original_content, feedback, master_context)
        elif component_type == ComponentType.AUDIO:
            return await self._revise_audio_content(original_content, feedback, master_context, package_id)
        elif component_type == ComponentType.PRACTICE:
            return await self._revise_practice_problems(original_content, feedback, master_context)
        else:
            raise ValueError(f"Unknown component type: {component_type}")

    async def _revise_reading_content(
        self,
        original_content: Dict[str, Any],
        feedback: str,
        master_context
    ) -> Dict[str, Any]:
        """Revise reading content based on feedback"""
        
        # Use same terminology for coherence
        terminology_str = "\n".join([f"- {term}: {defn}" for term, defn in master_context.key_terminology.items()])
        
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
                config=self.types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.4,
                    max_output_tokens=25000
                )
            )
            
            revised_content = json.loads(response.text)
            logger.info("Reading content revised successfully")
            return revised_content
            
        except Exception as e:
            logger.error(f"Reading content revision failed: {str(e)}")
            raise

    async def _revise_visual_demo(
        self,
        original_content: Dict[str, Any],
        feedback: str,
        master_context
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
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.5,
                    max_output_tokens=25000
                )
            )
            
            revised_content = json.loads(response.text)
            logger.info("Visual demo revised successfully")
            return revised_content
            
        except Exception as e:
            logger.error(f"Visual demo revision failed: {str(e)}")
            raise

    async def _revise_audio_content(
        self,
        original_content: Dict[str, Any],
        feedback: str,
        master_context,
        package_id: str
    ) -> Dict[str, Any]:
        """Revise audio content - script and regenerate audio"""
        
        # Use same terminology for coherence
        terminology_str = "\n".join([f"- {term}: {defn}" for term, defn in master_context.key_terminology.items()])
        
        prompt = f"""
        Revise this educational dialogue script based on the feedback provided.

        ORIGINAL SCRIPT: {original_content.get('dialogue_script', '')}

        FEEDBACK TO ADDRESS: {feedback}

        REQUIREMENTS (maintain coherence):
        - Use the same key terminology: {terminology_str}
        - Cover the same core concepts: {', '.join(master_context.core_concepts)}
        - Address the same learning objectives: {', '.join(master_context.learning_objectives)}
        - Keep natural teacher-student conversation format
        - Maintain appropriate length (450-750 words when spoken)
        
        Apply the feedback while maintaining educational coherence.
        Return ONLY the revised dialogue script in the same format:
        Teacher: [what teacher says]  
        Student: [what student says]
        """
        
        try:
            # Generate revised script
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash-preview-05-20',
                contents=prompt,
                config=self.types.GenerateContentConfig(
                    temperature=0.6,
                    max_output_tokens=25000
                )
            )
            
            revised_script = response.text.strip()
            
            # Generate new audio with revised script (reuse existing audio generation)
            audio_component = await self._generate_and_store_audio(revised_script, package_id + "_rev")
            
            logger.info("Audio content revised and regenerated successfully")
            return audio_component.content
            
        except Exception as e:
            logger.error(f"Audio content revision failed: {str(e)}")
            raise

    async def _revise_practice_problems(
        self,
        original_content: Dict[str, Any],
        feedback: str,
        master_context
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
                config=self.types.GenerateContentConfig(
                    response_mime_type='application/json',
                    temperature=0.5,
                    max_output_tokens=16000
                )
            )
            
            revised_content = json.loads(response.text)
            logger.info("Practice problems revised successfully")
            return revised_content
            
        except Exception as e:
            logger.error(f"Practice problems revision failed: {str(e)}")
            raise

    def _serialize_datetime_fields(self, data):
        """
        Recursively convert all datetime objects to ISO format strings
        """
        if isinstance(data, dict):
            return {key: self._serialize_datetime_fields(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._serialize_datetime_fields(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data