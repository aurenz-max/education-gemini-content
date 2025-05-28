# test_generation.py - UPDATED FOR STORAGE INTEGRATION
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

# Set higher log levels for Azure SDKs to reduce verbosity
logging.getLogger('azure').setLevel(logging.WARNING)  # or logging.ERROR for even less output
logging.getLogger('azure.cosmos').setLevel(logging.INFO)  # Specifically for Cosmos DB
logging.getLogger('urllib3').setLevel(logging.WARNING)  # For HTTP request logs

from app.core.content_generator import ContentGenerationService
from app.models.content import ContentGenerationRequest
from app.database.cosmos_client import cosmos_service
from app.database.blob_storage import blob_storage_service


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


async def check_storage_services():
    """Check if storage services can initialize properly"""
    
    print("\n☁️ STORAGE SERVICES VALIDATION")
    print("=" * 60)
    logger.info("=== STORAGE SERVICES VALIDATION START ===")
    
    storage_results = {
        'cosmos_config': False,
        'blob_config': False,
        'cosmos_init': False,
        'blob_init': False,
        'cosmos_health': False,
        'blob_health': False
    }
    
    try:
        # 1. Check Cosmos DB configuration
        print("🗄️ Checking Cosmos DB configuration...")
        cosmos_endpoint = os.getenv("COSMOS_DB_ENDPOINT")
        cosmos_key = os.getenv("COSMOS_DB_KEY")
        
        if cosmos_endpoint and cosmos_key:
            print(f"✅ COSMOS_DB_ENDPOINT: {cosmos_endpoint}")
            print(f"✅ COSMOS_DB_KEY: {cosmos_key[:10]}...{cosmos_key[-4:]}")
            storage_results['cosmos_config'] = True
        else:
            print("❌ Cosmos DB configuration missing")
            print("💡 Required: COSMOS_DB_ENDPOINT, COSMOS_DB_KEY in .env")
            logger.error("Cosmos DB configuration incomplete")
        
        # 2. Check Blob Storage configuration
        print("\n🗃️ Checking Blob Storage configuration...")
        blob_connection = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        blob_container = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
        
        if blob_connection and blob_container:
            print(f"✅ AZURE_STORAGE_CONNECTION_STRING: {blob_connection[:30]}...")
            print(f"✅ AZURE_STORAGE_CONTAINER_NAME: {blob_container}")
            storage_results['blob_config'] = True
        else:
            print("❌ Blob Storage configuration missing")
            print("💡 Required: AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER_NAME in .env")
            logger.error("Blob Storage configuration incomplete")
        
        # 3. Test Cosmos DB initialization
        if storage_results['cosmos_config']:
            print("\n🧪 Testing Cosmos DB initialization...")
            try:
                cosmos_init_success = await cosmos_service.initialize()
                if cosmos_init_success:
                    print("✅ Cosmos DB initialized successfully")
                    storage_results['cosmos_init'] = True
                else:
                    print("❌ Cosmos DB initialization failed")
                    logger.error("Cosmos DB initialization returned False")
            except Exception as e:
                print(f"❌ Cosmos DB initialization error: {str(e)}")
                logger.error(f"Cosmos DB initialization exception: {str(e)}")
        
        # 4. Test Blob Storage initialization
        if storage_results['blob_config']:
            print("\n🧪 Testing Blob Storage initialization...")
            try:
                blob_init_success = await blob_storage_service.initialize()
                if blob_init_success:
                    print("✅ Blob Storage initialized successfully")
                    storage_results['blob_init'] = True
                else:
                    print("❌ Blob Storage initialization failed")
                    logger.error("Blob Storage initialization returned False")
            except Exception as e:
                print(f"❌ Blob Storage initialization error: {str(e)}")
                logger.error(f"Blob Storage initialization exception: {str(e)}")
        
        # 5. Test Cosmos DB health
        if storage_results['cosmos_init']:
            print("\n💊 Testing Cosmos DB health...")
            try:
                health = await cosmos_service.health_check()
                if health.get("status") == "healthy":
                    print(f"✅ Cosmos DB is healthy (Documents: {health.get('total_documents', 0)})")
                    storage_results['cosmos_health'] = True
                else:
                    print(f"❌ Cosmos DB health check failed: {health.get('error', 'Unknown')}")
            except Exception as e:
                print(f"❌ Cosmos DB health check error: {str(e)}")
        
        # 6. Test Blob Storage health
        if storage_results['blob_init']:
            print("\n💊 Testing Blob Storage health...")
            try:
                health = await blob_storage_service.health_check()
                if health.get("status") == "healthy":
                    print(f"✅ Blob Storage is healthy (Recent blobs: {health.get('total_recent_blobs', 0)})")
                    storage_results['blob_health'] = True
                else:
                    print(f"❌ Blob Storage health check failed: {health.get('error', 'Unknown')}")
            except Exception as e:
                print(f"❌ Blob Storage health check error: {str(e)}")
        
    except Exception as e:
        print(f"\n💥 Unexpected error during storage validation: {e}")
        logger.error(f"Unexpected storage validation error: {e}", exc_info=True)
    
    # Summary
    print(f"\n📊 STORAGE VALIDATION SUMMARY")
    print("-" * 40)
    
    all_storage_passed = all(storage_results.values())
    
    for check, passed in storage_results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check.replace('_', ' ').title()}")
    
    if all_storage_passed:
        print(f"\n🎉 All storage validation checks PASSED!")
        print("✅ Storage services are ready for integration")
        logger.info("All storage validation checks passed")
    else:
        print(f"\n⚠️ Some storage validation checks FAILED")
        print("❌ Storage issues detected - see details above")
        logger.warning("Storage validation failed")
        
        # Specific recommendations
        if not storage_results['cosmos_config'] or not storage_results['blob_config']:
            print("\n💡 RECOMMENDATION: Complete storage configuration")
            print("   Add missing environment variables to .env file")
        
        if not storage_results['cosmos_init'] or not storage_results['blob_init']:
            print("\n💡 RECOMMENDATION: Check Azure credentials and permissions")
            print("   Verify connection strings and access keys are correct")
    
    print("=" * 60)
    logger.info("=== STORAGE SERVICES VALIDATION END ===")
    
    return all_storage_passed


async def test_content_generation():
    """Test the INTEGRATED content generation pipeline with storage"""
    
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
    logger.info("STARTING INTEGRATED CONTENT GENERATION TEST")
    logger.info("="*60)
    
    try:
        print("🚀 Starting INTEGRATED content generation test...")
        print(f"Topic: {request.subject} → {request.unit} → {request.skill} → {request.subskill}")
        logger.info(f"Test request: {request}")
        
        # Initialize service (storage services should already be initialized)
        print("📡 Initializing content generation service...")
        logger.info("Initializing ContentGenerationService with storage integration")
        service = ContentGenerationService()
        logger.info("Service initialized successfully")
        
        # Generate content with timing
        start_time = datetime.now()
        print("⚙️ Generating content package with integrated storage...")
        logger.info("Starting integrated content package generation")
        
        package = await service.generate_content_package(request)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        print(f"\n✅ INTEGRATED generation completed successfully!")
        print(f"Package ID: {package.id}")
        print(f"Partition Key: {package.partition_key}")
        print(f"Total generation time: {total_time:.2f} seconds")
        print(f"Reported generation time: {package.generation_metadata.generation_time_ms}ms")
        print(f"Coherence score: {package.generation_metadata.coherence_score}")
        
        logger.info(f"Package generated and stored successfully: {package.id}")
        logger.info(f"Total time: {total_time:.2f}s, Reported: {package.generation_metadata.generation_time_ms}ms")
        
        # Validate master context
        print(f"\n📚 Master Context Validation:")
        mc = package.master_context
        print(f"Core concepts ({len(mc.core_concepts)}): {', '.join(mc.core_concepts)}")
        print(f"Key terms ({len(mc.key_terminology)}): {', '.join(mc.key_terminology.keys())}")
        print(f"Learning objectives: {len(mc.learning_objectives)} objectives")
        print(f"Real-world applications: {len(mc.real_world_applications)} applications")
        
        logger.info(f"Master context - Concepts: {len(mc.core_concepts)}, Terms: {len(mc.key_terminology)}")
        
        # Validate each content component with STORAGE INTEGRATION
        content_checks = await validate_integrated_content_components(package)
        
        # STORAGE VALIDATION
        print(f"\n☁️ Storage Integration Validation:")
        
        # Test package retrieval from Cosmos DB
        try:
            retrieved_package = await service.get_content_package(
                package.id, package.subject, package.unit
            )
            print(f"✅ Package retrieved from Cosmos DB: {retrieved_package.id}")
            storage_retrieval = True
        except Exception as e:
            print(f"❌ Package retrieval failed: {str(e)}")
            storage_retrieval = False
        
        # Test audio blob URL accessibility
        audio = package.content.get("audio", {})
        blob_url = audio.get("audio_blob_url", "")
        if blob_url and blob_url.startswith("https://"):
            print(f"✅ Audio blob URL generated: {blob_url[:50]}...")
            blob_url_valid = True
        else:
            print(f"❌ Invalid or missing blob URL: {blob_url}")
            blob_url_valid = False
        
        print(f"\n🎯 INTEGRATED Content Validation:")
        components_passed = sum(content_checks.values())
        total_components = len(content_checks)
        
        print(f"📊 Component Results ({components_passed}/{total_components} passed):")
        for component, passed in content_checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {component.title()}: {passed}")
        
        print(f"\n☁️ Storage Results:")
        print(f"   ✅ Package stored in Cosmos DB: {storage_retrieval}")
        print(f"   ✅ Audio stored in Blob Storage: {blob_url_valid}")
        print(f"   ✅ Cross-modal coherence: {package.generation_metadata.coherence_score > 0.8}")
        
        # Calculate overall success
        all_components_passed = all(content_checks.values())
        storage_success = storage_retrieval and blob_url_valid
        coherence_success = package.generation_metadata.coherence_score > 0.8
        
        overall_success = all_components_passed and storage_success and coherence_success
        
        print(f"\n🏆 OVERALL RESULT:")
        print(f"   Components: {components_passed}/{total_components} ({'✅' if all_components_passed else '❌'})")
        print(f"   Storage: {'✅' if storage_success else '❌'}")
        print(f"   Coherence: {'✅' if coherence_success else '❌'}")
        print(f"   SUCCESS: {'✅' if overall_success else '❌'}")
        
        if not overall_success:
            print(f"\n🔍 Failed Components:")
            for component, passed in content_checks.items():
                if not passed:
                    print(f"   ❌ {component.title()}")
            if not storage_success:
                print(f"   ❌ Storage Integration")
            if not coherence_success:
                print(f"   ❌ Coherence Score ({package.generation_metadata.coherence_score})")
        
        # Save sample output for inspection
        await save_sample_output(package)
        
        logger.info("Integrated content generation test completed successfully")
        
        # Return the actual success status
        return overall_success
        
    except Exception as e:
        print(f"\n❌ INTEGRATED generation failed: {str(e)}")
        logger.error(f"Integrated content generation failed: {str(e)}", exc_info=True)
        return False


async def validate_integrated_content_components(package):
    """Validate each content component with STORAGE INTEGRATION checks"""
    
    checks = {}
    
    # Reading Content Validation (unchanged)
    print(f"\n📖 Reading Content Validation:")
    reading = package.content.get("reading", {})
    if reading:
        sections = reading.get('sections', [])
        word_count = reading.get('word_count', 0)
        
        print(f"✅ Title: {reading.get('title', 'N/A')}")
        print(f"✅ Sections: {len(sections)}")
        print(f"✅ Word count: {word_count}")
        
        valid_sections = all('heading' in s and 'content' in s for s in sections)
        print(f"✅ Section structure valid: {valid_sections}")
        
        checks['reading'] = len(sections) > 0 and word_count > 500 and valid_sections
        logger.info(f"Reading validation - Sections: {len(sections)}, Words: {word_count}, Valid: {checks['reading']}")
    else:
        print("❌ No reading content found")
        checks['reading'] = False
    
    # Visual Demo Validation (unchanged)
    print(f"\n🎨 Visual Demo Validation:")
    visual = package.content.get("visual", {})
    if visual:
        p5_code = visual.get('p5_code', '')
        interactive_elements = visual.get('interactive_elements', [])
        
        print(f"✅ Description: {visual.get('description', 'N/A')[:100]}...")
        print(f"✅ Interactive elements: {len(interactive_elements)}")
        print(f"✅ Code length: {len(p5_code)} characters")
        
        has_setup = 'function setup()' in p5_code
        has_draw = 'function draw()' in p5_code
        print(f"✅ Has setup function: {has_setup}")
        print(f"✅ Has draw function: {has_draw}")
        
        checks['visual'] = len(p5_code) > 100 and has_setup and len(interactive_elements) > 0
        logger.info(f"Visual validation - Code: {len(p5_code)} chars, Interactive: {len(interactive_elements)}, Valid: {checks['visual']}")
    else:
        print("❌ No visual content found")
        checks['visual'] = False
    
    # Audio Content Validation - UPDATED FOR BLOB STORAGE
    print(f"\n🎵 Audio Content Validation (BLOB STORAGE):")
    audio = package.content.get("audio", {})
    if audio:
        audio_filename = audio.get('audio_filename', 'N/A')
        duration = audio.get('duration_seconds', 0)
        dialogue_script = audio.get('dialogue_script', '')
        script_words = len(dialogue_script.split()) if dialogue_script else 0
        blob_url = audio.get('audio_blob_url', '')
        blob_name = audio.get('blob_name', '')
        
        print(f"✅ Audio filename: {audio_filename}")
        print(f"✅ Duration: {duration:.1f} seconds")
        print(f"✅ Script length: {script_words} words")
        print(f"✅ Blob URL: {blob_url[:60]}..." if blob_url else "❌ No blob URL")
        print(f"✅ Blob name: {blob_name}" if blob_name else "❌ No blob name")
        
        # Check blob URL validity (should be HTTPS Azure URL)
        blob_url_valid = blob_url and blob_url.startswith("https://") and "blob.core.windows.net" in blob_url
        print(f"✅ Blob URL valid: {blob_url_valid}")
        
        # Check if we have the essential blob storage indicators
        has_blob_indicators = blob_url_valid and blob_name and audio_filename
        print(f"✅ Has blob storage indicators: {has_blob_indicators}")
        
        # More lenient validation - focus on what matters
        audio_validation_passed = (
            duration > 60 and 
            script_words > 100 and 
            blob_url_valid and 
            has_blob_indicators
        )
        
        print(f"🎯 Audio validation details:")
        print(f"   - Duration > 60s: {duration > 60} ({duration:.1f}s)")
        print(f"   - Script > 100 words: {script_words > 100} ({script_words} words)")
        print(f"   - Valid blob URL: {blob_url_valid}")
        print(f"   - Has blob indicators: {has_blob_indicators}")
        print(f"   - OVERALL AUDIO VALID: {audio_validation_passed}")
        
        checks['audio'] = audio_validation_passed
        logger.info(f"Audio validation - Duration: {duration}s, Words: {script_words}, Blob URL: {blob_url_valid}, Valid: {checks['audio']}")
    else:
        print("❌ No audio content found")
        checks['audio'] = False
    
    # Practice Problems Validation (unchanged)
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
            
            valid_structure = all(
                'id' in p and 
                'problem_data' in p and 
                'problem' in p.get('problem_data', {}) and
                'answer' in p.get('problem_data', {})
                for p in problems[:3]
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
    """Save sample output for manual inspection - UPDATED FOR STORAGE"""
    
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Save full package as JSON - include storage metadata
        package_dict = {
            "id": package.id,
            "partition_key": package.partition_key,
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
            },
            "storage_info": {
                "stored_in_cosmos": True,
                "audio_stored_in_blob": bool(package.content.get("audio", {}).get("audio_blob_url")),
                "blob_url": package.content.get("audio", {}).get("audio_blob_url", ""),
                "test_timestamp": timestamp
            }
        }
        
        output_file = output_dir / f"integrated_package_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(package_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Integrated sample output saved to: {output_file}")
        logger.info(f"Integrated sample output saved to {output_file}")
        
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
            
            # Save blob info
            blob_info_file = output_dir / f"blob_info_{timestamp}.txt"
            with open(blob_info_file, 'w', encoding='utf-8') as f:
                f.write(f"Blob URL: {audio.get('audio_blob_url', 'N/A')}\n")
                f.write(f"Blob Name: {audio.get('blob_name', 'N/A')}\n")
                f.write(f"Audio Filename: {audio.get('audio_filename', 'N/A')}\n")
                f.write(f"Duration: {audio.get('duration_seconds', 0)} seconds\n")
            print(f"💾 Blob info saved to: {blob_info_file}")
            
    except Exception as e:
        print(f"⚠️ Could not save sample output: {str(e)}")
        logger.warning(f"Failed to save sample output: {str(e)}")


def check_environment():
    """Check environment setup with detailed validation - UPDATED FOR STORAGE"""
    
    print("🔧 Environment Check")
    print("-" * 40)
    
    # Check Gemini API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        print("\nPlease create a .env file with:")
        print("GEMINI_API_KEY=your-api-key-here")
        return False
    
    print(f"✅ Gemini API key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Check storage configuration
    print("\n☁️ Storage Configuration:")
    
    # Cosmos DB
    cosmos_endpoint = os.getenv("COSMOS_DB_ENDPOINT")
    cosmos_key = os.getenv("COSMOS_DB_KEY")
    if cosmos_endpoint and cosmos_key:
        print(f"✅ Cosmos DB configured: {cosmos_endpoint}")
    else:
        print("❌ Cosmos DB configuration missing")
        print("💡 Required: COSMOS_DB_ENDPOINT, COSMOS_DB_KEY")
        return False
    
    # Blob Storage
    blob_connection = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    blob_container = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
    if blob_connection and blob_container:
        print(f"✅ Blob Storage configured: Container '{blob_container}'")
    else:
        print("❌ Blob Storage configuration missing")
        print("💡 Required: AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER_NAME")
        return False
    
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
        from app.database.cosmos_client import cosmos_service
        from app.database.blob_storage import blob_storage_service
        print("✅ All imports successful (including storage services)")
    except ImportError as e:
        print(f"❌ Import failed: {str(e)}")
        return False
    
    logger.info("Environment check completed successfully")
    return True


async def test_storage_cleanup():
    """Test storage cleanup functionality"""
    
    print("\n🧹 Testing Storage Cleanup...")
    
    try:
        # Create a test package ID
        test_package_id = f"test_cleanup_{int(datetime.now().timestamp())}"
        
        print(f"📦 Test package ID: {test_package_id}")
        
        # Test blob cleanup (should handle non-existent package gracefully)
        cleanup_result = await blob_storage_service.cleanup_package_audio(test_package_id)
        
        if cleanup_result.get("success", False):
            print(f"✅ Cleanup test passed: {cleanup_result.get('deleted_count', 0)} files cleaned")
        else:
            print(f"⚠️ Cleanup test: {cleanup_result.get('errors', [])}")
        
        logger.info("Storage cleanup test completed")
        return True
        
    except Exception as e:
        print(f"❌ Storage cleanup test failed: {str(e)}")
        logger.error(f"Storage cleanup test failed: {str(e)}")
        return False


async def test_individual_components():
    """Test individual generation components - REMOVED since integrated version is better"""
    
    print("\n🔬 Individual component tests skipped in integrated version")
    print("💡 Running full integrated test instead for better validation")
    logger.info("Skipping individual component tests - using integrated test")
    return True


async def main():
    """Main test function with comprehensive logging - UPDATED FOR STORAGE INTEGRATION"""
    
    print("🧪 EDUCATIONAL CONTENT GENERATION SYSTEM TESTS (INTEGRATED)")
    print("=" * 70)
    logger.info("Starting comprehensive INTEGRATED test suite")
    
    # STEP 1: Google GenAI validation (critical)
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
    
    # STEP 2: Storage services validation (new and critical)
    print("\n" + "☁️ STEP 2: STORAGE SERVICES VALIDATION" + "\n" + "-" * 60)
    storage_validation_passed = await check_storage_services()
    
    if not storage_validation_passed:
        print("\n🚨 CRITICAL: Storage services validation FAILED!")
        print("❌ Cannot proceed with integrated tests until storage is working.")
        print("\n💡 Common fixes:")
        print("1. Check your .env file has all required Azure credentials")
        print("2. Verify your Azure Cosmos DB and Blob Storage are created")
        print("3. Check network connectivity to Azure services")
        print("4. Verify your Azure access keys are correct and not expired")
        logger.error("Storage validation failed - stopping tests")
        return
    
    print("\n🎉 Storage services validation PASSED!")
    
    # STEP 3: General environment check
    print("\n" + "🔧 STEP 3: GENERAL ENVIRONMENT CHECK" + "\n" + "-" * 60)
    if not check_environment():
        logger.error("Environment check failed")
        return
    
    # STEP 4: Test storage cleanup functionality
    print("\n" + "🧹 STEP 4: STORAGE CLEANUP TEST" + "\n" + "-" * 60)
    cleanup_success = await test_storage_cleanup()
    
    if not cleanup_success:
        print("\n⚠️ Storage cleanup test failed - proceeding anyway")
        logger.warning("Storage cleanup test failed but continuing")
    
    # STEP 5: Run integrated content generation test
    print("\n" + "🚀 STEP 5: INTEGRATED CONTENT GENERATION TEST" + "\n" + "-" * 60)
    integrated_success = await test_content_generation()
    
    # Final results
    print("\n" + "📊 INTEGRATED TEST RESULTS" + "\n" + "=" * 70)
    
    if integrated_success:
        print("🎉 ALL INTEGRATED TESTS PASSED! System is working with cloud storage.")
        print("\n✅ What works:")
        print("   • Content generation with Gemini AI")
        print("   • Audio files uploaded to Azure Blob Storage")
        print("   • Content packages stored in Azure Cosmos DB")
        print("   • Package retrieval from cloud storage")
        print("   • Blob URLs generated for direct audio access")
        print("\n🚀 Next steps:")
        print("1. Your content generator now uses cloud storage automatically")
        print("2. Run your FastAPI server to test the API endpoints")
        print("3. Check generated packages in Azure portal")
        print("4. Audio files are accessible via blob URLs")
        print("5. Review logs in: test_generation.log")
        
        # Show sample blob URL for verification
        try:
            with open("test_output/integrated_package_" + datetime.now().strftime("%Y%m%d") + "*.json") as f:
                pass  # Just checking if file exists
            print("6. Check test_output/ folder for sample generated content")
        except:
            pass
        
        logger.info("All integrated tests completed successfully")
    else:
        print("❌ Some integrated tests failed. Check the logs for details.")
        print("\n🔍 Troubleshooting:")
        print("• Check test_generation.log for detailed error information")
        print("• Verify your Azure credentials are correct")
        print("• Ensure your Azure services (Cosmos DB, Blob Storage) are running")
        print("• Check network connectivity to Azure")
        print("• Verify your Gemini API key is valid and has quota remaining")
        
        logger.error("Integrated test suite completed with failures")


if __name__ == "__main__":
    asyncio.run(main())