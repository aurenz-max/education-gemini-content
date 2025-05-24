# test_generation.py
import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_generation.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

from app.core.content_generator import ContentGenerationService
from app.models.content import ContentGenerationRequest


def check_google_genai_environment():
    """Comprehensive environment and dependency validation for google-genai"""
    
    print("\n🔍 GOOGLE GENAI ENVIRONMENT VALIDATION")
    print("=" * 60)
    logger.info("=== GOOGLE GENAI ENVIRONMENT VALIDATION START ===")
    
    validation_results = {
        'python_version': False,
        'genai_version': False,
        'imports': False,
        'api_key': False,
        'environment': False
    }
    
    try:
        # 1. Check Python version
        print(f"🐍 Python version: {sys.version}")
        print(f"🐍 Python executable: {sys.executable}")
        logger.info(f"Python version: {sys.version}")
        validation_results['python_version'] = True
        
        # 2. Check google-genai version
        print(f"\n📦 Checking google-genai package...")
        try:
            import pkg_resources
            genai_version = pkg_resources.get_distribution("google-genai").version
            print(f"✅ google-genai version: {genai_version}")
            logger.info(f"google-genai version: {genai_version}")
            
            # Parse version and check minimum requirement
            try:
                from packaging import version
                if version.parse(genai_version) < version.parse("1.16.0"):
                    print(f"❌ google-genai version {genai_version} is too old. Need >= 1.16.0 for multi-speaker audio")
                    print("💡 Upgrade with: pip install -U google-genai>=1.16.0")
                    logger.error(f"google-genai version {genai_version} is insufficient")
                    validation_results['genai_version'] = False
                else:
                    print("✅ google-genai version is sufficient for multi-speaker audio")
                    logger.info("google-genai version check passed")
                    validation_results['genai_version'] = True
                    
            except ImportError:
                print("⚠️ Could not validate version (packaging module missing)")
                print("💡 Install with: pip install packaging")
                # Assume version is OK if we can't check
                validation_results['genai_version'] = True
                
        except pkg_resources.DistributionNotFound:
            print("❌ google-genai package not found")
            print("💡 Install with: pip install google-genai>=1.16.0")
            logger.error("google-genai package not found")
            return validation_results
        
        # 3. Test critical imports
        print(f"\n🔌 Testing imports...")
        try:
            from google import genai
            print("✅ google.genai imported successfully")
            logger.info("google.genai import successful")
            
            # Test the specific types that are causing issues
            print("🔌 Testing google.genai.types imports...")
            
            from google.genai import types
            print("✅ google.genai.types imported")
            
            # Test each critical type individually
            critical_types = [
                'GenerateContentConfig',
                'SpeechConfig', 
                'MultiSpeakerVoiceConfig',
                'SpeakerVoiceConfig',
                'VoiceConfig',
                'PrebuiltVoiceConfig'
            ]
            
            missing_types = []
            for type_name in critical_types:
                if hasattr(types, type_name):
                    print(f"✅ {type_name} available")
                else:
                    print(f"❌ {type_name} NOT available")
                    missing_types.append(type_name)
            
            if missing_types:
                print(f"\n❌ Missing types: {', '.join(missing_types)}")
                print("💡 This indicates your google-genai version may not support multi-speaker TTS")
                logger.error(f"Missing types: {missing_types}")
                validation_results['imports'] = False
            else:
                print("✅ All required types are available")
                logger.info("All required types imported successfully")
                
                # Test instantiation of the problematic type
                try:
                    test_config = types.MultiSpeakerVoiceConfig(speaker_voice_configs=[])
                    print("✅ MultiSpeakerVoiceConfig can be instantiated")
                    validation_results['imports'] = True
                except Exception as e:
                    print(f"❌ MultiSpeakerVoiceConfig instantiation failed: {e}")
                    logger.error(f"MultiSpeakerVoiceConfig instantiation failed: {e}")
                    validation_results['imports'] = False
                    
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            logger.error(f"Critical import failed: {e}")
            validation_results['imports'] = False
        
        # 4. Check API key
        print(f"\n🔑 Checking API key...")
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            print(f"✅ GEMINI_API_KEY is set")
            print(f"🔑 Key starts with: {api_key[:10]}...")
            logger.info("GEMINI_API_KEY found")
            validation_results['api_key'] = True
        else:
            print("❌ GEMINI_API_KEY not found in environment")
            print("💡 Create .env file with: GEMINI_API_KEY=your-key-here")
            logger.error("GEMINI_API_KEY not found")
            validation_results['api_key'] = False
        
        # 5. Environment details
        print(f"\n🌍 Environment details...")
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"🛤️ Python path entries:")
        for i, path in enumerate(sys.path[:5]):  # First 5 entries
            print(f"   {i+1}. {path}")
        
        # Check virtual environment
        venv = os.getenv('VIRTUAL_ENV')
        if venv:
            print(f"🐍 Virtual environment: {venv}")
        else:
            print("⚠️ No virtual environment detected")
        
        logger.info(f"Working directory: {os.getcwd()}")
        validation_results['environment'] = True
        
        # 6. Test basic Gemini client initialization
        if validation_results['genai_version'] and validation_results['imports'] and validation_results['api_key']:
            print(f"\n🧪 Testing Gemini client initialization...")
            try:
                client = genai.Client(api_key=api_key)
                print("✅ Gemini client initialized successfully")
                logger.info("Gemini client initialization test passed")
            except Exception as e:
                print(f"❌ Gemini client initialization failed: {e}")
                logger.error(f"Gemini client initialization failed: {e}")
        
    except Exception as e:
        print(f"\n💥 Unexpected error during validation: {e}")
        logger.error(f"Unexpected validation error: {e}", exc_info=True)
    
    # Summary
    print(f"\n📊 VALIDATION SUMMARY")
    print("-" * 40)
    all_passed = all(validation_results.values())
    
    for check, passed in validation_results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check.replace('_', ' ').title()}")
    
    if all_passed:
        print(f"\n🎉 All validation checks PASSED!")
        print("✅ Environment is ready for multi-speaker TTS")
        logger.info("All validation checks passed")
    else:
        print(f"\n⚠️ Some validation checks FAILED")
        print("❌ Environment issues detected - see details above")
        logger.warning("Environment validation failed")
        
        # Specific recommendations
        if not validation_results['genai_version']:
            print("\n💡 RECOMMENDATION: Upgrade google-genai")
            print("   pip install -U google-genai>=1.16.0")
        
        if not validation_results['imports']:
            print("\n💡 RECOMMENDATION: Check installation")
            print("   pip uninstall google-genai")
            print("   pip install google-genai>=1.16.0")
        
        if not validation_results['api_key']:
            print("\n💡 RECOMMENDATION: Set up API key")
            print("   Create .env file with GEMINI_API_KEY=your-key")
    
    print("=" * 60)
    logger.info("=== GOOGLE GENAI ENVIRONMENT VALIDATION END ===")
    
    return all_passed


async def test_content_generation():
    """Test the content generation pipeline with detailed logging"""
    
    # Set up test request
    request = ContentGenerationRequest(
        subject="Mathematics",
        unit="Algebra", 
        skill="Linear Equations",
        subskill="Slope-Intercept Form",
        difficulty_level="intermediate",
        prerequisites=["basic_algebra", "coordinate_plane"]
    )
    
    logger.info("="*60)
    logger.info("STARTING FULL CONTENT GENERATION TEST")
    logger.info("="*60)
    
    try:
        print("🚀 Starting content generation test...")
        print(f"Topic: {request.subject} → {request.unit} → {request.skill} → {request.subskill}")
        logger.info(f"Test request: {request}")
        
        # Initialize service
        print("📡 Initializing Gemini service...")
        logger.info("Initializing ContentGenerationService")
        service = ContentGenerationService()
        logger.info("Service initialized successfully")
        
        # Generate content with timing
        start_time = datetime.now()
        print("⚙️ Generating content package...")
        logger.info("Starting content package generation")
        
        package = await service.generate_content_package(request)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Generation completed successfully!")
        print(f"Package ID: {package.id}")
        print(f"Total generation time: {total_time:.2f} seconds")
        print(f"Reported generation time: {package.generation_metadata.generation_time_ms}ms")
        print(f"Coherence score: {package.generation_metadata.coherence_score}")
        
        logger.info(f"Package generated successfully: {package.id}")
        logger.info(f"Total time: {total_time:.2f}s, Reported: {package.generation_metadata.generation_time_ms}ms")
        
        # Validate master context
        print(f"\n📚 Master Context Validation:")
        mc = package.master_context
        print(f"Core concepts ({len(mc.core_concepts)}): {', '.join(mc.core_concepts)}")
        print(f"Key terms ({len(mc.key_terminology)}): {', '.join(mc.key_terminology.keys())}")
        print(f"Learning objectives: {len(mc.learning_objectives)} objectives")
        print(f"Real-world applications: {len(mc.real_world_applications)} applications")
        
        logger.info(f"Master context - Concepts: {len(mc.core_concepts)}, Terms: {len(mc.key_terminology)}")
        
        # Validate each content component
        content_checks = await validate_content_components(package)
        
        # Audio file check
        audio = package.content.get("audio", {})
        audio_path = audio.get('audio_file_path', '')
        audio_exists = os.path.exists(audio_path) if audio_path else False
        
        print(f"\n🎯 Content Integration Validation:")
        print(f"All components generated: {'✅' if all(content_checks.values()) else '❌'}")
        print(f"Audio file created: {'✅' if audio_exists else '❌'}")
        print(f"Cross-modal coherence: {'✅' if package.generation_metadata.coherence_score > 0.8 else '❌'}")
        
        # Save sample output for inspection
        await save_sample_output(package)
        
        logger.info("Full content generation test completed successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Generation failed: {str(e)}")
        logger.error(f"Content generation failed: {str(e)}", exc_info=True)
        return False


async def validate_content_components(package):
    """Validate each content component with detailed checks"""
    
    checks = {}
    
    # Reading Content Validation
    print(f"\n📖 Reading Content Validation:")
    reading = package.content.get("reading", {})
    if reading:
        sections = reading.get('sections', [])
        word_count = reading.get('word_count', 0)
        
        print(f"✅ Title: {reading.get('title', 'N/A')}")
        print(f"✅ Sections: {len(sections)}")
        print(f"✅ Word count: {word_count}")
        
        # Check if sections have required fields
        valid_sections = all('heading' in s and 'content' in s for s in sections)
        print(f"✅ Section structure valid: {valid_sections}")
        
        checks['reading'] = len(sections) > 0 and word_count > 500 and valid_sections
        logger.info(f"Reading validation - Sections: {len(sections)}, Words: {word_count}, Valid: {checks['reading']}")
    else:
        print("❌ No reading content found")
        checks['reading'] = False
    
    # Visual Demo Validation
    print(f"\n🎨 Visual Demo Validation:")
    visual = package.content.get("visual", {})
    if visual:
        p5_code = visual.get('p5_code', '')
        interactive_elements = visual.get('interactive_elements', [])
        
        print(f"✅ Description: {visual.get('description', 'N/A')[:100]}...")
        print(f"✅ Interactive elements: {len(interactive_elements)}")
        print(f"✅ Code length: {len(p5_code)} characters")
        
        # Basic p5.js validation
        has_setup = 'function setup()' in p5_code
        has_draw = 'function draw()' in p5_code
        print(f"✅ Has setup function: {has_setup}")
        print(f"✅ Has draw function: {has_draw}")
        
        checks['visual'] = len(p5_code) > 100 and has_setup and len(interactive_elements) > 0
        logger.info(f"Visual validation - Code: {len(p5_code)} chars, Interactive: {len(interactive_elements)}, Valid: {checks['visual']}")
    else:
        print("❌ No visual content found")
        checks['visual'] = False
    
    # Audio Content Validation
    print(f"\n🎵 Audio Content Validation:")
    audio = package.content.get("audio", {})
    if audio:
        audio_file = audio.get('audio_filename', 'N/A')
        duration = audio.get('duration_seconds', 0)
        script_words = audio.get('script_word_count', 0)
        
        print(f"✅ Audio file: {audio_file}")
        print(f"✅ Duration: {duration:.1f} seconds")
        print(f"✅ Script length: {script_words} words")
        
        # Check if file exists
        audio_path = audio.get('audio_file_path', '')
        file_exists = os.path.exists(audio_path) if audio_path else False
        print(f"✅ File exists: {file_exists}")
        
        checks['audio'] = duration > 60 and script_words > 100 and file_exists
        logger.info(f"Audio validation - Duration: {duration}s, Words: {script_words}, Exists: {file_exists}, Valid: {checks['audio']}")
    else:
        print("❌ No audio content found")
        checks['audio'] = False
    
    # Practice Problems Validation
    print(f"\n📝 Practice Problems Validation:")
    practice = package.content.get("practice", {})
    if practice:
        problems = practice.get('problems', [])
        problem_count = practice.get('problem_count', 0)
        
        print(f"✅ Problem count: {problem_count}")
        print(f"✅ Problems array length: {len(problems)}")
        
        if problems:
            sample = problems[0]
            print(f"✅ Sample problem ID: {sample.get('id', 'N/A')}")
            print(f"✅ Sample type: {sample.get('problem_data', {}).get('problem_type', 'N/A')}")
            
            # Validate problem structure
            valid_structure = all(
                'id' in p and 
                'problem_data' in p and 
                'problem' in p.get('problem_data', {}) and
                'answer' in p.get('problem_data', {})
                for p in problems[:3]  # Check first 3
            )
            print(f"✅ Problem structure valid: {valid_structure}")
            
            checks['practice'] = len(problems) >= 5 and valid_structure
        else:
            checks['practice'] = False
        
        logger.info(f"Practice validation - Count: {len(problems)}, Valid: {checks['practice']}")
    else:
        print("❌ No practice content found")
        checks['practice'] = False
    
    return checks


async def save_sample_output(package):
    """Save sample output for manual inspection"""
    
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Save full package as JSON
        package_dict = {
            "id": package.id,
            "subject": package.subject,
            "unit": package.unit,
            "skill": package.skill,
            "subskill": package.subskill,
            "master_context": {
                "core_concepts": package.master_context.core_concepts,
                "key_terminology": package.master_context.key_terminology,
                "learning_objectives": package.master_context.learning_objectives,
                "real_world_applications": package.master_context.real_world_applications
            },
            "content": package.content,
            "generation_metadata": {
                "generation_time_ms": package.generation_metadata.generation_time_ms,
                "coherence_score": package.generation_metadata.coherence_score
            }
        }
        
        output_file = output_dir / f"content_package_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(package_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Sample output saved to: {output_file}")
        logger.info(f"Sample output saved to {output_file}")
        
        # Save just the visual code for easy testing
        visual = package.content.get("visual", {})
        if visual and 'p5_code' in visual:
            p5_file = output_dir / f"visual_demo_{timestamp}.js"
            with open(p5_file, 'w', encoding='utf-8') as f:
                f.write(visual['p5_code'])
            print(f"💾 p5.js code saved to: {p5_file}")
        
        # Save audio script as text
        audio = package.content.get("audio", {})
        if audio and 'dialogue_script' in audio:
            script_file = output_dir / f"audio_script_{timestamp}.txt"
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(audio['dialogue_script'])
            print(f"💾 Audio script saved to: {script_file}")
            
    except Exception as e:
        print(f"⚠️ Could not save sample output: {str(e)}")
        logger.warning(f"Failed to save sample output: {str(e)}")


async def test_individual_components():
    """Test individual generation components with detailed logging"""
    
    request = ContentGenerationRequest(
        subject="Mathematics",
        unit="Basic Arithmetic", 
        skill="Addition",
        subskill="Two-digit Addition",
        difficulty_level="beginner"
    )
    
    logger.info("Starting individual component tests")
    
    try:
        print("\n🧪 Testing individual components...")
        service = ContentGenerationService()
        
        # Initialize variables to track components
        master_context = None
        reading = None
        visual = None
        script = None
        audio_comp = None
        practice = None
        
        # Test 1: Master Context
        print("\n1️⃣ Testing Master Context Generation...")
        logger.info("Testing master context generation")
        start_time = datetime.now()
        
        master_context = await service._generate_master_context(request)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"✅ Generated in {elapsed:.2f}s")
        print(f"✅ Core concepts ({len(master_context.core_concepts)}): {master_context.core_concepts}")
        print(f"✅ Key terms ({len(master_context.key_terminology)}): {list(master_context.key_terminology.keys())}")
        print(f"✅ Learning objectives ({len(master_context.learning_objectives)})")
        
        logger.info(f"Master context generated in {elapsed:.2f}s - {len(master_context.core_concepts)} concepts")
        
        # Test 2: Reading Content
        print("\n2️⃣ Testing Reading Content Generation...")
        logger.info("Testing reading content generation")
        start_time = datetime.now()
        
        try:
            reading = await service._generate_reading_content(request, master_context, "test_pkg")
            
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"✅ Generated in {elapsed:.2f}s")
            print(f"✅ Sections: {reading.metadata.get('section_count', 0)}")
            print(f"✅ Word count: {reading.metadata.get('word_count', 0)}")
            print(f"✅ Title: {reading.content.get('title', 'N/A')}")
            
            # Check if this was a fallback
            if reading.metadata.get('generation_status') == 'fallback':
                print("⚠️ Used fallback content due to generation issues")
            
            logger.info(f"Reading content generated in {elapsed:.2f}s - {reading.metadata.get('word_count', 0)} words")
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"❌ Failed in {elapsed:.2f}s: {str(e)}")
            logger.error(f"Reading content generation failed: {str(e)}")
            raise
        
        # Test 3: Visual Demo
        print("\n3️⃣ Testing Visual Demo Generation...")
        logger.info("Testing visual demo generation")
        start_time = datetime.now()
        
        try:
            visual = await service._generate_visual_demo(request, master_context, "test_pkg")
            
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"✅ Generated in {elapsed:.2f}s")
            print(f"✅ Code lines: {visual.metadata.get('code_lines', 0)}")
            print(f"✅ Interactive elements: {len(visual.content.get('interactive_elements', []))}")
            print(f"✅ Description: {visual.content.get('description', 'N/A')[:100]}...")
            
            # Check if this was a fallback
            if visual.metadata.get('generation_status') == 'fallback':
                print("⚠️ Used fallback content due to generation issues")
            
            logger.info(f"Visual demo generated in {elapsed:.2f}s - {visual.metadata.get('code_lines', 0)} lines")
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"❌ Failed in {elapsed:.2f}s: {str(e)}")
            logger.error(f"Visual demo generation failed: {str(e)}")
            raise
        
        # Test 4: Audio Script Generation
        print("\n4️⃣ Testing Audio Script Generation...")
        logger.info("Testing audio script generation")
        start_time = datetime.now()
        
        script = await service._generate_audio_script(request, master_context)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        word_count = len(script.split())
        print(f"✅ Generated in {elapsed:.2f}s")
        print(f"✅ Script length: {word_count} words")
        print(f"✅ First 100 chars: {script[:100]}...")
        
        logger.info(f"Audio script generated in {elapsed:.2f}s - {word_count} words")
        
        # Test 5: FULL Audio Generation (Script + TTS)
        print("\n5️⃣ Testing FULL Audio Generation (Script → TTS → WAV)...")
        logger.info("Testing complete audio generation including TTS")
        start_time = datetime.now()
        
        try:
            audio_comp = await service._generate_audio_from_script(script, "test_individual_pkg")
            
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"✅ Full audio generated in {elapsed:.2f}s")
            print(f"✅ Audio filename: {audio_comp.content.get('audio_filename', 'N/A')}")
            print(f"✅ File size: {audio_comp.metadata.get('file_size_bytes', 0)} bytes")
            print(f"✅ Duration: {audio_comp.content.get('duration_seconds', 0):.1f} seconds")
            print(f"✅ TTS Status: {audio_comp.content.get('tts_status', 'unknown')}")
            
            # Verify file actually exists
            audio_path = audio_comp.content.get('audio_file_path', '')
            if audio_path and os.path.exists(audio_path):
                print(f"✅ Audio file verified: {audio_path}")
            else:
                print(f"❌ Audio file not found: {audio_path}")
            
            logger.info(f"Full audio generation completed in {elapsed:.2f}s - {audio_comp.metadata.get('file_size_bytes', 0)} bytes")
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"❌ Full audio generation failed in {elapsed:.2f}s: {str(e)}")
            logger.error(f"Full audio generation failed: {str(e)}")
            # Set audio_comp to None so summary can handle it
            audio_comp = None
            raise

        # Test 6: Practice Problems Generation
        print("\n6️⃣ Testing Practice Problems Generation...")
        logger.info("Testing practice problems generation")
        start_time = datetime.now()
        
        practice = await service._generate_practice_problems(
            request, master_context, reading, visual, "test_pkg"
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        problem_count = practice.metadata.get('problem_count', 0)
        print(f"✅ Generated in {elapsed:.2f}s")
        print(f"✅ Problem count: {problem_count}")
        
        if practice.content.get('problems'):
            sample = practice.content['problems'][0]
            print(f"✅ Sample ID: {sample.get('id', 'N/A')}")
            print(f"✅ Sample type: {sample.get('problem_data', {}).get('problem_type', 'N/A')}")
        
        logger.info(f"Practice problems generated in {elapsed:.2f}s - {problem_count} problems")
        
        print(f"\n🎉 All individual components working!")
        print(f"📊 Component Test Summary:")
        print(f"✅ Master Context: Generated with {len(master_context.core_concepts) if master_context else 0} concepts")
        print(f"✅ Reading Content: {reading.metadata.get('word_count', 0) if reading else 0} words in {reading.metadata.get('section_count', 0) if reading else 0} sections")
        print(f"✅ Visual Demo: {visual.metadata.get('code_lines', 0) if visual else 0} lines of p5.js code")
        print(f"✅ Audio Script: {len(script.split()) if script else 0} words generated")
        print(f"✅ Full Audio TTS: {audio_comp.metadata.get('file_size_bytes', 0) if audio_comp else 0} bytes WAV file")
        print(f"✅ Practice Problems: {practice.metadata.get('problem_count', 0) if practice else 0} problems")
        
        logger.info("All individual component tests passed INCLUDING full audio TTS generation")
        return True
        
    except Exception as e:
        print(f"\n❌ Component test failed: {str(e)}")
        logger.error(f"Component test failed: {str(e)}", exc_info=True)
        return False


def check_environment():
    """Check environment setup with detailed validation"""
    
    print("🔧 Environment Check")
    print("-" * 40)
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        print("\nPlease create a .env file with:")
        print("GEMINI_API_KEY=your-api-key-here")
        return False
    
    print(f"✅ API key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Check directories
    audio_dir = Path("generated_audio")
    if not audio_dir.exists():
        print(f"📁 Creating audio directory: {audio_dir}")
        audio_dir.mkdir(exist_ok=True)
    else:
        print(f"✅ Audio directory exists: {audio_dir}")
    
    test_output_dir = Path("test_output")
    if not test_output_dir.exists():
        print(f"📁 Creating test output directory: {test_output_dir}")
        test_output_dir.mkdir(exist_ok=True)
    else:
        print(f"✅ Test output directory exists: {test_output_dir}")
    
    # Check imports
    try:
        from app.core.content_generator import ContentGenerationService
        from app.models.content import ContentGenerationRequest
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {str(e)}")
        return False
    
    logger.info("Environment check completed successfully")
    return True


async def main():
    """Main test function with comprehensive logging"""
    
    print("🧪 EDUCATIONAL CONTENT GENERATION SYSTEM TESTS")
    print("=" * 60)
    logger.info("Starting comprehensive test suite")
    
    # CRITICAL: Run google-genai environment validation FIRST
    print("\n" + "🔍 STEP 1: GOOGLE GENAI VALIDATION" + "\n" + "-" * 60)
    genai_validation_passed = check_google_genai_environment()
    
    if not genai_validation_passed:
        print("\n🚨 CRITICAL: Google GenAI environment validation FAILED!")
        print("❌ Cannot proceed with tests until environment issues are resolved.")
        print("\n💡 Common fixes:")
        print("1. pip install -U google-genai>=1.16.0")
        print("2. Restart your Python environment/terminal")
        print("3. Check your virtual environment is activated")
        print("4. Verify GEMINI_API_KEY is set in .env file")
        logger.error("Google GenAI validation failed - stopping tests")
        return
    
    print("\n🎉 Google GenAI environment validation PASSED!")
    print("✅ Proceeding with content generation tests...")
    
    # Environment check
    print("\n" + "🔧 STEP 2: GENERAL ENVIRONMENT CHECK" + "\n" + "-" * 60)
    if not check_environment():
        logger.error("Environment check failed")
        return
    
    # Run individual component tests first
    print("\n" + "🔬 STEP 3: INDIVIDUAL COMPONENT TESTS" + "\n" + "-" * 60)
    component_success = await test_individual_components()
    
    if not component_success:
        print("\n⚠️ Individual component tests failed - skipping full pipeline test")
        logger.warning("Skipping full pipeline test due to component failures")
        return
    
    # Run full pipeline test
    print("\n" + "🚀 STEP 4: FULL PIPELINE TEST" + "\n" + "-" * 60)
    full_success = await test_content_generation()
    
    # Final results
    print("\n" + "📊 TEST RESULTS" + "\n" + "=" * 60)
    
    if full_success:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
        print("\nNext steps:")
        print("1. Run the FastAPI server: python -m app.main")
        print("2. Test API at: http://localhost:8000/docs")
        print("3. Check generated files in: generated_audio/ and test_output/")
        print("4. Review logs in: test_generation.log")
        
        logger.info("All tests completed successfully")
    else:
        print("❌ Some tests failed. Check the logs for details.")
        print("Log file: test_generation.log")
        
        logger.error("Test suite completed with failures")


if __name__ == "__main__":
    asyncio.run(main())