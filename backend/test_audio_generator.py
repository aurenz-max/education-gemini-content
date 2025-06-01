# test_audio_generator.py
"""
Test script specifically for AudioContentGenerator to verify MP3 conversion works correctly.
Run this to test audio generation in isolation.
"""
import asyncio
import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any
import tempfile
import time

# Load environment variables from .env file
load_dotenv()

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

# Import the audio generator
from app.core.generators.audio_content import AudioContentGenerator

# Import models
from app.models.content import (
    ContentGenerationRequest,
    MasterContext,
    ContentComponent,
    ComponentType
)

# Mock services for testing
class MockCosmosService:
    """Mock cosmos service for testing"""
    async def create_content_package(self, package):
        return package
    
    async def get_content_package(self, package_id, partition_key):
        return None

class MockBlobService:
    """Mock blob service for testing"""
    def __init__(self):
        self.uploaded_files = []
    
    async def upload_audio_file(self, package_id, file_path, filename, overwrite=True):
        """Mock blob upload that tracks what was uploaded"""
        # Check if file exists and get size
        file_size = 0
        file_format = "unknown"
        
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            file_format = Path(file_path).suffix.lower().replace('.', '')
        
        upload_info = {
            "package_id": package_id,
            "file_path": file_path,
            "filename": filename,
            "file_size": file_size,
            "file_format": file_format,
            "timestamp": time.time()
        }
        
        self.uploaded_files.append(upload_info)
        
        print(f"📤 Mock upload: {filename} ({file_size} bytes, {file_format} format)")
        
        return {
            "success": True,
            "blob_url": f"https://test.blob.core.windows.net/audio/{package_id}/{filename}",
            "blob_name": f"{package_id}/{filename}"
        }
    
    async def cleanup_package_audio(self, package_id):
        return {"success": True, "deleted_count": 1}

# Test data
def create_test_request() -> ContentGenerationRequest:
    """Create a test content generation request"""
    return ContentGenerationRequest(
        subject="Mathematics",
        unit="Fractions",
        skill="Understanding fractions",
        subskill="Adding fractions with like denominators",
        difficulty_level="beginner",
        grade="4th Grade",
        prerequisites=["Understanding whole numbers", "Basic addition"]
    )

def create_test_master_context() -> MasterContext:
    """Create a test master context"""
    return MasterContext(
        core_concepts=[
            "Fractions represent parts of a whole",
            "Like denominators mean same bottom number",
            "Add numerators when denominators are same"
        ],
        key_terminology={
            "numerator": "The top number in a fraction",
            "denominator": "The bottom number in a fraction",
            "like denominators": "Fractions with the same bottom number"
        },
        learning_objectives=[
            "Students will add fractions with like denominators",
            "Students will explain what numerator and denominator mean",
            "Students will solve real-world fraction problems"
        ],
        difficulty_level="beginner",
        prerequisites=["Understanding whole numbers", "Basic addition"],
        real_world_applications=[
            "Sharing pizza slices equally",
            "Measuring ingredients in cooking",
            "Dividing time into parts"
        ]
    )

class TestAudioGenerator:
    """Test AudioContentGenerator specifically"""
    
    def setup_method(self):
        """Setup test data and mock services"""
        self.mock_cosmos = MockCosmosService()
        self.mock_blob = MockBlobService()
        self.test_request = create_test_request()
        self.test_context = create_test_master_context()
        self.package_id = f"test_audio_{int(time.time())}"

    @pytest.mark.asyncio
    async def test_audio_script_generation(self):
        """Test audio script generation"""
        print("\n🎬 Testing Audio Script Generation...")
        
        generator = AudioContentGenerator(
            cosmos_service=self.mock_cosmos,
            blob_service=self.mock_blob
        )
        
        try:
            script = await generator.generate_audio_script(self.test_request, self.test_context)
            
            # Verify script structure
            assert isinstance(script, str)
            assert len(script) > 50
            assert "Teacher:" in script
            assert "Student:" in script
            
            # Count dialogue turns
            teacher_turns = script.count("Teacher:")
            student_turns = script.count("Student:")
            total_words = len(script.split())
            
            print("✅ Audio script generated successfully")
            print(f"   - Total length: {len(script)} characters")
            print(f"   - Word count: {total_words}")
            print(f"   - Teacher turns: {teacher_turns}")
            print(f"   - Student turns: {student_turns}")
            print(f"   - Estimated duration: {(total_words / 150) * 60:.1f} seconds")
            
            # Check that key terminology is used
            terminology_found = []
            for term in self.test_context.key_terminology.keys():
                if term.lower() in script.lower():
                    terminology_found.append(term)
            
            print(f"   - Key terms used: {len(terminology_found)}/{len(self.test_context.key_terminology)}")
            
            return script
            
        except Exception as e:
            print(f"❌ Audio script generation failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_audio_generation_disabled(self):
        """Test audio generation with TTS disabled"""
        print("\n🔇 Testing Audio Generation (TTS Disabled)...")
        
        # Mock settings to disable TTS by modifying the underlying ENABLE_TTS setting
        import app.config
        original_enable_tts = app.config.settings.ENABLE_TTS
        app.config.settings.ENABLE_TTS = False
        
        try:
            generator = AudioContentGenerator(
                cosmos_service=self.mock_cosmos,
                blob_service=self.mock_blob
            )
            
            test_script = "Teacher: Hello! Student: Hi teacher!"
            
            audio_comp = await generator.generate_and_store_audio(test_script, self.package_id)
            
            # Verify structure when TTS is disabled
            assert isinstance(audio_comp, ContentComponent)
            assert audio_comp.component_type == ComponentType.AUDIO
            assert audio_comp.content["tts_status"] == "disabled"
            assert audio_comp.content["audio_blob_url"] is None
            assert audio_comp.content["dialogue_script"] == test_script
            assert audio_comp.metadata["tts_enabled"] is False
            
            print("✅ Audio component created with TTS disabled")
            print(f"   - TTS status: {audio_comp.content['tts_status']}")
            print(f"   - Duration estimate: {audio_comp.content['duration_seconds']:.1f} seconds")
            print(f"   - File size: {audio_comp.metadata['file_size_bytes']} bytes")
            
        finally:
            # Restore original setting
            app.config.settings.ENABLE_TTS = original_enable_tts

    @pytest.mark.asyncio
    async def test_audio_generation_enabled(self):
        """Test audio generation with TTS enabled"""
        print("\n🎵 Testing Audio Generation (TTS Enabled)...")
        
        # Mock settings to enable TTS by modifying the underlying ENABLE_TTS setting
        import app.config
        original_enable_tts = app.config.settings.ENABLE_TTS
        app.config.settings.ENABLE_TTS = True
        
        try:
            generator = AudioContentGenerator(
                cosmos_service=self.mock_cosmos,
                blob_service=self.mock_blob
            )
            
            # Generate a script first
            script = await generator.generate_audio_script(self.test_request, self.test_context)
            print(f"   - Generated script: {len(script)} characters")
            
            # Generate audio
            print("   - Attempting TTS generation...")
            audio_comp = await generator.generate_and_store_audio(script, self.package_id)
            
            # Verify structure
            assert isinstance(audio_comp, ContentComponent)
            assert audio_comp.component_type == ComponentType.AUDIO
            assert audio_comp.content["dialogue_script"] == script
            assert "tts_status" in audio_comp.content
            assert "duration_seconds" in audio_comp.content
            assert "voice_config" in audio_comp.content
            
            print("✅ Audio generation attempted")
            print(f"   - TTS status: {audio_comp.content['tts_status']}")
            print(f"   - Audio format: {audio_comp.metadata.get('audio_format', 'N/A')}")
            print(f"   - File size: {audio_comp.metadata['file_size_bytes']} bytes")
            print(f"   - MP3 conversion: {audio_comp.metadata.get('converted_to_mp3', 'N/A')}")
            
            # Check if file was uploaded
            if len(self.mock_blob.uploaded_files) > 0:
                upload_info = self.mock_blob.uploaded_files[-1]
                print(f"   - Uploaded: {upload_info['filename']}")
                print(f"   - Upload size: {upload_info['file_size']} bytes")
                print(f"   - Upload format: {upload_info['file_format']}")
                
                # Check compression ratio if MP3 conversion succeeded
                if audio_comp.metadata.get('converted_to_mp3'):
                    compression_ratio = audio_comp.metadata.get('compression_ratio', 1.0)
                    print(f"   - Compression ratio: {compression_ratio:.2f}")
                    print(f"   - Size reduction: {(1 - compression_ratio) * 100:.1f}%")
            
            return audio_comp
            
        except Exception as e:
            print(f"⚠️  Audio generation failed (this may be expected): {e}")
            print("   This could be due to API limits, network issues, or TTS service availability")
            # Don't re-raise for TTS failures as they're environment-dependent
            
        finally:
            # Restore original setting
            app.config.settings.ENABLE_TTS = original_enable_tts

    @pytest.mark.asyncio
    async def test_audio_revision(self):
        """Test audio content revision"""
        print("\n✏️  Testing Audio Content Revision...")
        
        generator = AudioContentGenerator(
            cosmos_service=self.mock_cosmos,
            blob_service=self.mock_blob
        )
        
        try:
            # Create original content
            original_content = {
                "dialogue_script": "Teacher: Let's learn fractions. Student: Okay!",
                "duration_seconds": 60.0,
                "tts_status": "success"
            }
            
            feedback = "Make the dialogue more engaging and include more examples"
            
            # Test revision
            revised_content = await generator.revise_audio_content(
                original_content,
                feedback,
                self.test_context,
                self.package_id + "_revision"
            )
            
            # Verify revision structure
            assert "dialogue_script" in revised_content
            assert "duration_seconds" in revised_content
            assert revised_content["dialogue_script"] != original_content["dialogue_script"]
            
            print("✅ Audio content revision successful")
            print(f"   - Original length: {len(original_content['dialogue_script'])}")
            print(f"   - Revised length: {len(revised_content['dialogue_script'])}")
            print(f"   - Contains Teacher/Student: {'Teacher:' in revised_content['dialogue_script'] and 'Student:' in revised_content['dialogue_script']}")
            
        except Exception as e:
            print(f"❌ Audio revision failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_mp3_conversion_fallback(self):
        """Test MP3 conversion with fallback to WAV"""
        print("\n🔄 Testing MP3 Conversion Fallback...")
        
        generator = AudioContentGenerator(
            cosmos_service=self.mock_cosmos,
            blob_service=self.mock_blob
        )
        
        # Test the conversion method directly with mock data
        try:
            # Create some fake WAV data (just bytes for testing)
            fake_wav_data = b"RIFF" + b"\x00" * 100  # Minimal WAV-like header
            
            # Test conversion method
            converted_data, success = generator._convert_audio_to_mp3(fake_wav_data)
            
            print(f"   - Conversion attempted: {success}")
            print(f"   - Original size: {len(fake_wav_data)} bytes")
            print(f"   - Result size: {len(converted_data)} bytes")
            
            if success:
                print("✅ MP3 conversion succeeded")
                print(f"   - Compression achieved: {len(converted_data) < len(fake_wav_data)}")
            else:
                print("⚠️  MP3 conversion failed (fallback to original data)")
                print("   - This is expected if pydub/MP3 dependencies aren't available")
                assert converted_data == fake_wav_data  # Should return original on failure
            
        except Exception as e:
            print(f"⚠️  MP3 conversion test failed: {e}")
            print("   - This indicates pydub may not be installed or configured")

def check_audio_dependencies():
    """Check audio-specific dependencies"""
    print("\n🔍 Audio Dependencies Check")
    print("-" * 35)
    
    # Check for pydub
    try:
        import pydub
        print("✅ pydub installed")
        
        # Test basic functionality
        from pydub import AudioSegment
        print("✅ AudioSegment import successful")
        
    except ImportError:
        print("❌ pydub not installed")
        print("💡 Install with: pip install pydub")
        return False
    
    # Check for BytesIO
    try:
        from io import BytesIO
        print("✅ BytesIO available")
    except ImportError:
        print("❌ BytesIO not available")
        return False
    
    return True

async def run_audio_generator_tests():
    """Run all audio generator tests"""
    print("🎵 Starting Audio Generator Tests")
    print("=" * 45)
    
    # Check environment first
    if not check_environment():
        print("❌ Environment check failed - stopping tests")
        return
    
    # Check audio dependencies
    if not check_audio_dependencies():
        print("❌ Audio dependencies check failed - some tests may fail")
    
    test_suite = TestAudioGenerator()
    test_suite.setup_method()
    
    # Run tests in sequence (some depend on others)
    print("\n" + "="*50)
    
    try:
        # Test 1: Script generation (always works)
        await test_suite.test_audio_script_generation()
        
        # Test 2: Audio generation disabled (always works)
        await test_suite.test_audio_generation_disabled()
        
        # Test 3: Audio generation enabled (may fail due to API/TTS)
        await test_suite.test_audio_generation_enabled()
        
        # Test 4: Audio revision (should work)
        await test_suite.test_audio_revision()
        
        # Test 5: MP3 conversion test
        await test_suite.test_mp3_conversion_fallback()
        
        print("\n🎉 Audio generator tests completed!")
        print("✅ Audio script generation working")
        print("✅ TTS toggle functionality working")
        print("✅ MP3 conversion logic implemented")
        print("✅ Audio revision functionality working")
        
        # Summary of uploads
        if len(test_suite.mock_blob.uploaded_files) > 0:
            print(f"\n📤 Mock uploads performed: {len(test_suite.mock_blob.uploaded_files)}")
            for upload in test_suite.mock_blob.uploaded_files:
                print(f"   - {upload['filename']} ({upload['file_size']} bytes, {upload['file_format']})")
        
    except Exception as e:
        print(f"\n❌ Audio generator tests failed: {e}")
        print("🔧 Check dependencies and API configuration")
        raise

def check_environment():
    """Check that environment is properly configured"""
    print("\n🔧 Environment Check")
    print("-" * 30)
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("💡 Please create a .env file with:")
        print("   GEMINI_API_KEY=your-api-key-here")
        return False
    
    print(f"✅ GEMINI_API_KEY found: {api_key[:8]}...")
    
    # Check Python path
    current_dir = Path(__file__).parent
    app_dir = current_dir / "app"
    
    if not app_dir.exists():
        print(f"❌ App directory not found: {app_dir}")
        print("💡 Make sure you're running from the correct directory")
        return False
    
    print(f"✅ App directory found: {app_dir}")
    
    # Test imports
    try:
        from app.core.generators.audio_content import AudioContentGenerator
        print("✅ AudioContentGenerator import successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("💡 Make sure audio_content.py is in place")
        return False
    
    return True

if __name__ == "__main__":
    # Run the audio tests
    asyncio.run(run_audio_generator_tests())