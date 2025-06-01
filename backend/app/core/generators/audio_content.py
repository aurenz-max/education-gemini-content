# backend/app/core/generators/audio_content.py
import logging
from pathlib import Path
from typing import Dict, Any
import tempfile
import os
from pydub import AudioSegment
from io import BytesIO
from google.genai.types import (
    GenerateContentConfig,
    SpeechConfig,
    MultiSpeakerVoiceConfig,
    SpeakerVoiceConfig,
    VoiceConfig,
    PrebuiltVoiceConfig
)

from .base_generator import BaseContentGenerator
from app.models.content import ContentGenerationRequest, MasterContext, ContentComponent, ComponentType
from app.config import settings

logger = logging.getLogger(__name__)


class AudioContentGenerator(BaseContentGenerator):
    """Generator for audio content including dialogue scripts and TTS audio"""
    
    def _convert_raw_audio_to_wav(self, audio_data: bytes, mime_type: str = "audio/L16;rate=24000") -> bytes:
        """Convert raw PCM audio data to WAV format using Google's approach"""
        import struct
        
        # Parse audio parameters from mime type
        bits_per_sample = 16
        sample_rate = 24000
        
        # Extract rate from parameters (e.g., "audio/L16;rate=24000")
        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate_str = param.split("=", 1)[1]
                    sample_rate = int(rate_str)
                except (ValueError, IndexError):
                    pass
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass
        
        # WAV file parameters
        num_channels = 1
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size
        
        # Create WAV header
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",          # ChunkID
            chunk_size,       # ChunkSize (total file size - 8 bytes)
            b"WAVE",          # Format
            b"fmt ",          # Subchunk1ID
            16,               # Subchunk1Size (16 for PCM)
            1,                # AudioFormat (1 for PCM)
            num_channels,     # NumChannels
            sample_rate,      # SampleRate
            byte_rate,        # ByteRate
            block_align,      # BlockAlign
            bits_per_sample,  # BitsPerSample
            b"data",          # Subchunk2ID
            data_size         # Subchunk2Size (size of audio data)
        )
        
        return header + audio_data

    def _convert_audio_to_mp3(self, audio_data: bytes, mime_type: str = "audio/L16;rate=24000") -> tuple[bytes, bool]:
        """Convert raw PCM audio data to MP3 using pydub"""
        try:
            # First convert raw PCM to WAV format
            wav_data = self._convert_raw_audio_to_wav(audio_data, mime_type)
            
            # Load WAV audio from bytes
            audio_segment = AudioSegment.from_wav(BytesIO(wav_data))
            
            # Convert to MP3 with good quality settings
            mp3_buffer = BytesIO()
            audio_segment.export(
                mp3_buffer,
                format="mp3",
                bitrate="128k",
                parameters=["-ac", "2"]  # Force stereo
            )
            
            mp3_data = mp3_buffer.getvalue()
            logger.info(f"Successfully converted audio to MP3 (size: {len(mp3_data)} bytes)")
            return mp3_data, True
            
        except Exception as e:
            logger.error(f"Pydub MP3 conversion failed: {str(e)}")
            # Return WAV data as fallback
            try:
                wav_data = self._convert_raw_audio_to_wav(audio_data, mime_type)
                return wav_data, False
            except Exception:
                return audio_data, False

    async def generate_audio_script(
        self, request: ContentGenerationRequest, master_context: MasterContext
    ) -> str:
        """Generate dialogue script for audio content - UPDATED WITH GRADE"""
        
        terminology_str = self._format_terminology_string(master_context.key_terminology)
        grade_info = self._extract_grade_info(request)
        
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
                config=GenerateContentConfig(
                    temperature=0.6,
                    max_output_tokens=25000
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            self._handle_generation_error("Audio script generation", e)

    async def generate_and_store_audio(self, script: str, package_id: str) -> ContentComponent:
        """Generate audio and upload to blob storage - WITH PYDUB MP3 CONVERSION"""
        
        grade_info = "appropriate grade level"  # Could be extracted from request if needed
        
        # Check if TTS is enabled
        if not settings.tts_enabled:
            logger.info(f"TTS disabled - creating audio component with script only for package: {package_id}")
            
            # Calculate estimated duration
            word_count = len(script.split())
            estimated_duration = (word_count / 150) * 60  # 150 words per minute
            
            return ContentComponent(
                package_id=package_id,
                component_type=ComponentType.AUDIO,
                content={
                    "audio_blob_url": None,
                    "audio_filename": None,
                    "dialogue_script": script,
                    "duration_seconds": estimated_duration,
                    "voice_config": {
                        "teacher_voice": settings.DEFAULT_TEACHER_VOICE,
                        "student_voice": settings.DEFAULT_STUDENT_VOICE
                    },
                    "tts_status": "disabled",
                    "blob_name": None
                },
                metadata={
                    "duration_seconds": estimated_duration,
                    "file_size_bytes": 0,
                    "script_word_count": word_count,
                    "audio_format": None,
                    "tts_success": False,
                    "stored_in_blob": False,
                    "tts_enabled": False
                }
            )
        
        # TTS is enabled - proceed with audio generation
        audio_dir = Path("generated_audio")
        audio_dir.mkdir(exist_ok=True)
        
        logger.info(f"Generating audio for package: {package_id}")
        
        temp_file_path = None
        
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
            
            # Extract audio data and mime type
            audio_data = bytearray()
            mime_type = "audio/L16;rate=24000"  # Default
            
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
                    # Try to get mime type from the response
                    if hasattr(part.inline_data, 'mime_type') and part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
            
            if len(audio_data) == 0:
                raise ValueError("No audio data found in TTS response")
            
            logger.info(f"Extracted {len(audio_data)} bytes of audio data with mime type: {mime_type}")
            
            # Convert to MP3 using pydub (handles raw PCM -> WAV -> MP3)
            logger.info("Converting audio to MP3 format...")
            final_audio_data, conversion_success = self._convert_audio_to_mp3(bytes(audio_data), mime_type)
            
            # Determine filename and format
            if conversion_success:
                audio_filename = f"audio_{package_id}.mp3"
                final_format = "mp3"
                logger.info(f"Successfully converted to MP3. Size: original={len(audio_data)} final={len(final_audio_data)} bytes")
            else:
                # Fallback to WAV if conversion fails
                audio_filename = f"audio_{package_id}.wav"
                final_format = "wav"
                logger.warning("Using WAV format as MP3 conversion failed")
            
            # Save to temporary file for upload
            temp_file_path = str(audio_dir / audio_filename)
            with open(temp_file_path, 'wb') as f:
                f.write(final_audio_data)
            
            # Upload to blob storage
            logger.info(f"Uploading {final_format.upper()} audio to blob storage: {audio_filename}")
            upload_result = await self.blob_service.upload_audio_file(
                package_id=package_id,
                file_path=temp_file_path,
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
                    "file_size_bytes": len(final_audio_data),
                    "script_word_count": word_count,
                    "audio_format": final_format,
                    "tts_success": True,
                    "stored_in_blob": True,
                    "tts_enabled": True,
                    "converted_to_mp3": conversion_success,
                    "compression_ratio": round(len(final_audio_data) / len(audio_data), 2) if conversion_success else 1.0
                }
            )
            
        except Exception as e:
            self._handle_generation_error(f"Audio generation and storage for package {package_id}", e)
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")

    async def revise_audio_content(
        self,
        original_content: Dict[str, Any],
        feedback: str,
        master_context: MasterContext,
        package_id: str
    ) -> Dict[str, Any]:
        """Revise audio content - script and regenerate audio"""
        
        # Use same terminology for coherence
        terminology_str = self._format_terminology_string(master_context.key_terminology)
        
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
                config=GenerateContentConfig(
                    temperature=0.6,
                    max_output_tokens=25000
                )
            )
            
            revised_script = response.text.strip()
            
            # Generate new audio with revised script (reuse existing audio generation)
            audio_component = await self.generate_and_store_audio(revised_script, package_id + "_rev")
            
            logger.info("Audio content revised and regenerated successfully")
            return audio_component.content
            
        except Exception as e:
            self._handle_generation_error("Audio content revision", e)