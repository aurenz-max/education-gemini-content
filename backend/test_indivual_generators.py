# test_individual_generators.py
"""
Test script for individual generators to verify modularization works correctly.
Run this BEFORE testing the full pipeline.
"""
import asyncio
import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

# Import the new generators
from app.core.generators import (
    MasterContextGenerator,
    ReadingContentGenerator,
    VisualDemoGenerator,
    AudioContentGenerator,
    PracticeProblemsGenerator
)

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
    async def upload_audio_file(self, package_id, file_path, filename, overwrite=True):
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

class TestIndividualGenerators:
    """Test each generator independently"""
    
    def setup_method(self):
        """Setup test data and mock services"""
        self.mock_cosmos = MockCosmosService()
        self.mock_blob = MockBlobService()
        self.test_request = create_test_request()
        self.test_context = create_test_master_context()
        self.package_id = "test_pkg_123"

    @pytest.mark.asyncio
    async def test_master_context_generator(self):
        """Test MasterContextGenerator works independently"""
        print("\n🧪 Testing MasterContextGenerator...")
        
        generator = MasterContextGenerator(
            cosmos_service=self.mock_cosmos,
            blob_service=self.mock_blob
        )
        
        # Test context generation
        try:
            context = await generator.generate_master_context(self.test_request)
            
            # Verify structure
            assert isinstance(context, MasterContext)
            assert len(context.core_concepts) >= 3
            assert len(context.key_terminology) >= 3
            assert len(context.learning_objectives) >= 3
            assert context.difficulty_level is not None
            assert len(context.real_world_applications) >= 3
            
            print("✅ Master context generated successfully")
            print(f"   - Core concepts: {len(context.core_concepts)}")
            print(f"   - Key terms: {len(context.key_terminology)}")
            print(f"   - Learning objectives: {len(context.learning_objectives)}")
            
        except Exception as e:
            print(f"❌ Master context generation failed: {e}")
            raise

    @pytest.mark.asyncio 
    async def test_reading_content_generator(self):
        """Test ReadingContentGenerator works independently"""
        print("\n🧪 Testing ReadingContentGenerator...")
        
        generator = ReadingContentGenerator(
            cosmos_service=self.mock_cosmos,
            blob_service=self.mock_blob
        )
        
        try:
            # Test reading content generation
            reading_comp = await generator.generate_reading_content(
                self.test_request, self.test_context, self.package_id
            )
            
            # Verify structure
            assert isinstance(reading_comp, ContentComponent)
            assert reading_comp.component_type == ComponentType.READING
            assert reading_comp.package_id == self.package_id
            assert "title" in reading_comp.content
            assert "sections" in reading_comp.content
            assert len(reading_comp.content["sections"]) > 0
            
            print("✅ Reading content generated successfully")
            print(f"   - Sections: {len(reading_comp.content['sections'])}")
            print(f"   - Word count: {reading_comp.content.get('word_count', 'N/A')}")
            
            # Test revision functionality
            revised_content = await generator.revise_reading_content(
                reading_comp.content,
                "Make it more engaging for younger students",
                self.test_context
            )
            
            assert "title" in revised_content
            assert "sections" in revised_content
            print("✅ Reading content revision successful")
            
        except Exception as e:
            print(f"❌ Reading content generation failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_visual_demo_generator(self):
        """Test VisualDemoGenerator works independently"""
        print("\n🧪 Testing VisualDemoGenerator...")
        
        generator = VisualDemoGenerator(
            cosmos_service=self.mock_cosmos,
            blob_service=self.mock_blob
        )
        
        try:
            # Test p5.js code generation
            p5_code = await generator.generate_p5js_code(self.test_request, self.test_context)
            
            assert isinstance(p5_code, str)
            assert len(p5_code) > 100
            assert "function setup()" in p5_code or "setup()" in p5_code
            assert "function draw()" in p5_code or "draw()" in p5_code
            
            print("✅ P5.js code generated successfully")
            print(f"   - Code length: {len(p5_code)} characters")
            # Fix: Store the split result in a variable to avoid backslash in f-string
            code_lines = p5_code.split('\n')
            print(f"   - Lines: {len(code_lines)}")
            
            # Test metadata generation
            metadata = await generator.generate_visual_metadata(
                p5_code, self.test_request, self.test_context
            )
            
            assert "description" in metadata
            assert "interactive_elements" in metadata
            assert "concepts_demonstrated" in metadata
            assert len(metadata["interactive_elements"]) > 0
            
            print("✅ Visual metadata generated successfully")
            print(f"   - Interactive elements: {len(metadata['interactive_elements'])}")
            
            # Test complete demo generation
            visual_comp = await generator.generate_visual_demo(
                self.test_request, self.test_context, self.package_id
            )
            
            assert isinstance(visual_comp, ContentComponent)
            assert visual_comp.component_type == ComponentType.VISUAL
            assert "p5_code" in visual_comp.content
            assert "description" in visual_comp.content
            
            print("✅ Complete visual demo generated successfully")
            
        except Exception as e:
            print(f"❌ Visual demo generation failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_audio_content_generator(self):
        """Test AudioContentGenerator works independently"""
        print("\n🧪 Testing AudioContentGenerator...")
        
        generator = AudioContentGenerator(
            cosmos_service=self.mock_cosmos,
            blob_service=self.mock_blob
        )
        
        try:
            # Test script generation
            script = await generator.generate_audio_script(self.test_request, self.test_context)
            
            assert isinstance(script, str)
            assert len(script) > 50
            assert "Teacher:" in script
            assert "Student:" in script
            
            print("✅ Audio script generated successfully")
            print(f"   - Script length: {len(script)} characters")
            word_count = len(script.split())
            print(f"   - Word count: {word_count}")
            
            # Test audio generation (will use TTS toggle)
            audio_comp = await generator.generate_and_store_audio(script, self.package_id)
            
            assert isinstance(audio_comp, ContentComponent)
            assert audio_comp.component_type == ComponentType.AUDIO
            assert "dialogue_script" in audio_comp.content
            assert "duration_seconds" in audio_comp.content
            assert "tts_status" in audio_comp.content
            
            print("✅ Audio component generated successfully")
            print(f"   - TTS status: {audio_comp.content['tts_status']}")
            print(f"   - Duration: {audio_comp.content['duration_seconds']:.1f} seconds")
            
        except Exception as e:
            print(f"❌ Audio content generation failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_practice_problems_generator(self):
        """Test PracticeProblemsGenerator works independently"""
        print("\n🧪 Testing PracticeProblemsGenerator...")
        
        generator = PracticeProblemsGenerator(
            cosmos_service=self.mock_cosmos,
            blob_service=self.mock_blob
        )
        
        # Create mock reading and visual components
        mock_reading = ContentComponent(
            package_id=self.package_id,
            component_type=ComponentType.READING,
            content={
                "sections": [
                    {
                        "heading": "Understanding Fractions",
                        "concepts_covered": ["fractions as parts", "numerator and denominator"]
                    }
                ]
            },
            metadata={}
        )
        
        mock_visual = ContentComponent(
            package_id=self.package_id,
            component_type=ComponentType.VISUAL,
            content={
                "interactive_elements": ["fraction bars", "click to add", "visual feedback"]
            },
            metadata={}
        )
        
        try:
            # Test practice problems generation
            practice_comp = await generator.generate_practice_problems(
                self.test_request, self.test_context, mock_reading, mock_visual, self.package_id
            )
            
            assert isinstance(practice_comp, ContentComponent)
            assert practice_comp.component_type == ComponentType.PRACTICE
            assert "problems" in practice_comp.content
            assert "problem_count" in practice_comp.content
            assert len(practice_comp.content["problems"]) >= 5
            
            # Verify problem structure
            first_problem = practice_comp.content["problems"][0]
            assert "problem_data" in first_problem
            assert "problem_type" in first_problem["problem_data"]
            assert "problem" in first_problem["problem_data"]
            assert "answer" in first_problem["problem_data"]
            
            print("✅ Practice problems generated successfully")
            print(f"   - Problem count: {practice_comp.content['problem_count']}")
            print(f"   - Estimated time: {practice_comp.content['estimated_time_minutes']} minutes")
            
        except Exception as e:
            print(f"❌ Practice problems generation failed: {e}")
            raise

async def run_individual_generator_tests():
    """Run all individual generator tests"""
    print("🧪 Starting Individual Generator Tests")
    print("=" * 50)
    
    # Check environment first
    if not check_environment():
        print("❌ Environment check failed - stopping tests")
        return
    
    test_suite = TestIndividualGenerators()
    test_suite.setup_method()
    
    tests = [
        test_suite.test_master_context_generator(),
        test_suite.test_reading_content_generator(),
        test_suite.test_visual_demo_generator(),
        test_suite.test_audio_content_generator(),
        test_suite.test_practice_problems_generator()
    ]
    
    try:
        await asyncio.gather(*tests)
        print("\n🎉 All individual generator tests passed!")
        print("✅ Generators are working correctly in isolation")
        print("✅ Ready to test full pipeline integration")
        
    except Exception as e:
        print(f"\n❌ Generator tests failed: {e}")
        print("🔧 Fix issues before proceeding to integration tests")
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
        from app.core.generators import MasterContextGenerator
        print("✅ Generator imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("💡 Make sure all generator files are in place")
        return False
    
    return True

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_individual_generator_tests())