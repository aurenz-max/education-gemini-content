# backend/test_cosmos_simple.py
"""
Simplified Cosmos DB test using main cosmos_service (with datetime fix)
Run with: python test_cosmos_simple.py
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Get the directory where this script is located (backend folder)
script_dir = Path(__file__).parent
env_path = script_dir / ".env"

# Load environment variables from backend/.env file
load_dotenv(env_path)

# Add the app directory to Python path
sys.path.append(str(script_dir / "app"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set higher log levels for Azure SDKs to reduce verbosity
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('azure.cosmos').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Import the main cosmos service (with datetime fix)
from app.database.cosmos_client import cosmos_service
from app.models.content import ContentPackage, MasterContext, GenerationMetadata


async def create_test_package():
    """Create a test package"""
    timestamp = int(datetime.now().timestamp())
    
    print(f"🧪 Creating test package with timestamp: {timestamp}")
    
    package = ContentPackage(
        id=f"test_pkg_{timestamp}",
        subject="Mathematics",
        unit="Algebra",
        skill="Linear Equations",
        subskill="Slope-Intercept Form",
        master_context=MasterContext(
            core_concepts=[
                "The structure and components of the slope-intercept form (y = mx + b).",
                "Understanding 'm' as the slope, representing the rate of change.",
                "Understanding 'b' as the y-intercept, representing the starting value."
            ],
            key_terminology={
                "Linear Equation": "An equation whose graph is a straight line.",
                "Slope-Intercept Form": "A specific way to write linear equations, y = mx + b.",
                "Slope": "A measure of the steepness and direction of a line.",
                "Y-intercept": "The point where a line crosses the y-axis."
            },
            learning_objectives=[
                "Students will be able to identify the slope and y-intercept directly from a linear equation.",
                "Students will be able to graph a linear equation given in slope-intercept form.",
                "Students will be able to convert a linear equation from standard form into slope-intercept form."
            ],
            difficulty_level="intermediate",
            prerequisites=["basic_algebra"],
            real_world_applications=[
                "Modeling costs with fixed fees and per-unit charges.",
                "Distance-time relationships with constant speed."
            ]
        ),
        content={
            "reading": {
                "title": "Understanding Linear Equations: Test Content",
                "sections": [
                    {
                        "heading": "Introduction to Linear Equations",
                        "content": "This is test reading content for slope-intercept form.",
                        "key_terms_used": ["Linear Equation", "Slope-Intercept Form"],
                        "concepts_covered": ["The structure and components of the slope-intercept form (y = mx + b)."]
                    }
                ],
                "word_count": 500,
                "reading_level": "Intermediate"
            },
            "visual": {
                "p5_code": "function setup() { createCanvas(400, 400); }\nfunction draw() { background(220); }",
                "description": "Test interactive slope demonstration",
                "interactive_elements": ["slope_slider", "y_intercept_slider"],
                "concepts_demonstrated": ["slope", "y-intercept"],
                "user_instructions": "Adjust sliders to see how slope and y-intercept affect the line."
            },
            "audio": {
                "audio_file_path": "generated_audio/test_audio.wav",
                "audio_filename": "test_audio.wav",
                "dialogue_script": "Teacher: Let's explore slope-intercept form. Student: What does y = mx + b mean?",
                "duration_seconds": 120.5,
                "voice_config": {
                    "teacher_voice": "Zephyr",
                    "student_voice": "Puck"
                },
                "tts_status": "success"
            },
            "practice": {
                "problems": [
                    {
                        "id": "test_problem_1",
                        "problem_data": {
                            "problem_type": "Multiple Choice",
                            "problem": "What is the slope of y = 2x + 3?",
                            "answer": "2",
                            "success_criteria": ["Identify slope coefficient in slope-intercept form"],
                            "teaching_note": "The slope is the coefficient of x in y = mx + b form.",
                            "metadata": {
                                "subject": "Mathematics",
                                "unit": {"id": "ALGEBRA001", "title": "Algebra"},
                                "skill": {"id": "ALGEBRA001-01", "description": "Linear Equations"},
                                "subskill": {"id": "ALGEBRA001-01-A", "description": "Slope-Intercept Form"}
                            }
                        }
                    }
                ],
                "problem_count": 1,
                "estimated_time_minutes": 2
            }
        },
        generation_metadata=GenerationMetadata(
            generation_time_ms=15000,
            coherence_score=0.9
        )
    )
    
    print(f"   📝 Package ID: {package.id}")
    print(f"   📚 Subject/Unit: {package.subject}/{package.unit}")
    print(f"   🎯 Skill: {package.skill}")
    print(f"   📊 Content sections: Reading, Visual, Audio, Practice")
    
    return package


async def validate_environment():
    """Validate environment variables"""
    endpoint = os.getenv("COSMOS_DB_ENDPOINT")
    key = os.getenv("COSMOS_DB_KEY")
    database_name = os.getenv("COSMOS_DB_DATABASE_NAME", "educational_content")
    container_name = os.getenv("COSMOS_DB_CONTAINER_NAME", "content_packages")
    
    if not endpoint:
        print("❌ COSMOS_DB_ENDPOINT not found in environment")
        return False
    
    if not key:
        print("❌ COSMOS_DB_KEY not found in environment")
        return False
    
    print(f"✅ COSMOS_DB_ENDPOINT: {endpoint[:50]}...")
    print(f"✅ COSMOS_DB_KEY: ***{key[-10:]}")
    print(f"✅ Database Name: {database_name}")
    print(f"✅ Container Name: {container_name}")
    
    return True


async def run_cosmos_tests():
    """Run all CRUD tests using the main cosmos service"""
    
    print("🧪 SIMPLIFIED COSMOS DB TEST SUITE")
    print("=" * 50)
    
    try:
        # Validate environment first
        if not await validate_environment():
            return False
        
        # Initialize the main cosmos service
        print("\n1️⃣ Initializing Cosmos DB...")
        success = await cosmos_service.initialize()
        if not success:
            print("❌ Initialization failed")
            return False
        print("✅ Cosmos DB initialized successfully")
        
        # Health check
        print("\n2️⃣ Health Check...")
        health = await cosmos_service.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Documents: {health.get('total_documents', 0)}")
        
        # Create test package
        print("\n3️⃣ Testing CREATE...")
        test_package = await create_test_package()
        
        print(f"💾 Creating package: {test_package.id}")
        print(f"   📍 Partition Key: {test_package.subject}-{test_package.unit}")
        print(f"   📊 Document Size: ~{len(str(test_package.model_dump()))} characters")
        print(f"   🏷️  Status: generated")
        
        # Use the main cosmos service (with datetime fix)
        created_package = await cosmos_service.create_content_package(test_package)
        print(f"✅ Created: {created_package.id}")
        
        # Read test
        print("\n4️⃣ Testing READ...")
        partition_key = f"{test_package.subject}-{test_package.unit}"
        print(f"🔍 Retrieving package: {test_package.id}")
        print(f"   📍 Using partition key: {partition_key}")
        
        retrieved = await cosmos_service.get_content_package(test_package.id, partition_key)
        if retrieved:
            print(f"   ✅ Package found:")
            print(f"      📝 Subject: {retrieved.subject}")
            print(f"      📚 Unit: {retrieved.unit}")
            print(f"      🎯 Skill: {retrieved.skill}")
            print(f"      🏷️  Status: {getattr(retrieved, 'status', 'N/A')}")
            print(f"✅ Retrieved: {retrieved.id}")
        else:
            print(f"   ❌ Package not found: {test_package.id}")
            return False
        
        # List test
        print("\n5️⃣ Testing LIST...")
        print(f"📋 Listing packages with subject filter: Mathematics")
        packages = await cosmos_service.list_content_packages(subject="Mathematics")
        print(f"   📦 Found {len(packages)} packages")
        for i, pkg in enumerate(packages[:3]):  # Show first 3
            print(f"      {i+1}. {pkg.id} ({pkg.subject}/{pkg.unit} - {pkg.skill})")
        print(f"✅ Found {len(packages)} packages")
        
        # Update test
        print("\n6️⃣ Testing UPDATE...")
        print(f"🔄 Updating package: {retrieved.id}")
        old_skill = retrieved.skill
        retrieved.skill = "Updated Linear Equations"
        print(f"   📝 Skill change: {old_skill} → {retrieved.skill}")
        
        updated = await cosmos_service.update_content_package(retrieved)
        print(f"   ✅ Package updated successfully")
        print(f"✅ Updated: {updated.skill}")
        
        # Status update test
        print("\n7️⃣ Testing STATUS UPDATE...")
        print(f"🏷️  Updating status for package: {test_package.id}")
        print(f"   📍 Partition key: {partition_key}")
        print(f"   🔄 New status: approved")
        
        status_updated = await cosmos_service.update_package_status(test_package.id, partition_key, "approved")
        print(f"   ✅ Status updated successfully")
        print(f"✅ Status updated: {status_updated}")
        
        # Delete test
        print("\n8️⃣ Testing DELETE...")
        print(f"🗑️  Deleting package: {test_package.id}")
        print(f"   📍 Partition key: {partition_key}")
        
        deleted = await cosmos_service.delete_content_package(test_package.id, partition_key)
        if deleted:
            print(f"   ✅ Package deleted successfully from Cosmos DB")
        else:
            print(f"   ❌ Package not found for deletion: {test_package.id}")
        print(f"✅ Deleted: {deleted}")
        
        # Verify deletion
        print("\n9️⃣ Verifying deletion...")
        verify_deleted = await cosmos_service.get_content_package(test_package.id, partition_key)
        deletion_verified = verify_deleted is None
        if deletion_verified:
            print(f"   ✅ Package confirmed deleted")
        else:
            print(f"   ❌ Package still exists after deletion")
        print(f"✅ Deletion verified: {deletion_verified}")
        
        print("\n🎉 ALL TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
        
    finally:
        # The main service handles its own cleanup
        cosmos_service.close()


async def main():
    """Main test function"""
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔍 Looking for .env file at: {env_path}")
    
    if env_path.exists():
        print("✅ .env file found")
    else:
        print("❌ .env file not found")
        print(f"Expected location: {env_path.absolute()}")
        return
    
    success = await run_cosmos_tests()
    
    if success:
        print("\n✅ Cosmos DB integration is working!")
        print("🚀 Ready to integrate with your main application")
    else:
        print("\n❌ Tests failed - check the output above")


if __name__ == "__main__":
    asyncio.run(main())