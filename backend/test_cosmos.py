# backend/test_cosmos_simple.py
"""
Simplified Cosmos DB test using direct .env approach (like test_generation.py)
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
logging.getLogger('azure').setLevel(logging.WARNING)  # or logging.ERROR for even less output
logging.getLogger('azure.cosmos').setLevel(logging.INFO)  # Specifically for Cosmos DB
logging.getLogger('urllib3').setLevel(logging.WARNING)  # For HTTP request logs

# Direct imports - no config file dependency
from app.models.content import ContentPackage, MasterContext, GenerationMetadata

# Direct Azure Cosmos imports
from azure.cosmos import CosmosClient, PartitionKey, exceptions
import hashlib
import json


class DirectCosmosService:
    """Direct Cosmos DB service without config file dependency"""
    
    def __init__(self):
        # Get credentials directly from environment
        self.endpoint = os.getenv("COSMOS_DB_ENDPOINT")
        self.key = os.getenv("COSMOS_DB_KEY")
        self.database_name = os.getenv("COSMOS_DB_DATABASE_NAME", "educational_content")
        self.container_name = os.getenv("COSMOS_DB_CONTAINER_NAME", "content_packages")
        
        self.client = None
        self.database = None
        self.container = None
        self._initialized = False
    
    def validate_credentials(self):
        """Validate that we have the required credentials"""
        if not self.endpoint:
            print("❌ COSMOS_DB_ENDPOINT not found in environment")
            return False
        
        if not self.key:
            print("❌ COSMOS_DB_KEY not found in environment")
            return False
        
        print(f"✅ COSMOS_DB_ENDPOINT: {self.endpoint[:50]}...")
        print(f"✅ COSMOS_DB_KEY: ***{self.key[-10:]}")
        print(f"✅ Database Name: {self.database_name}")
        print(f"✅ Container Name: {self.container_name}")
        
        return True
    
    async def initialize(self):
        """Initialize Cosmos DB connection"""
        try:
            if not self.validate_credentials():
                return False
            
            print("🔌 Creating Cosmos DB client...")
            self.client = CosmosClient(self.endpoint, self.key)
            
            print("🗄️ Creating/getting database...")
            self.database = self.client.create_database_if_not_exists(id=self.database_name)
            
            print("📦 Creating/getting container...")
            self.container = self.database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/partition_key"),
                offer_throughput=400
            )
            
            self._initialized = True
            print("✅ Cosmos DB initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Cosmos DB initialization failed: {e}")
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def health_check(self):
        """Simple health check"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        try:
            # Count documents
            query = "SELECT VALUE COUNT(1) FROM c"
            items = list(self.container.query_items(query, enable_cross_partition_query=True))
            count = items[0] if items else 0
            
            return {
                "status": "healthy",
                "total_documents": count,
                "database": self.database_name,
                "container": self.container_name
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _add_storage_metadata(self, document, is_update=False):
        """Add storage metadata"""
        now = datetime.now(timezone.utc).isoformat()
        
        if not is_update:
            document["storage_metadata"] = {
                "created_at": now,
                "updated_at": now,
                "version": 1
            }
        else:
            if "storage_metadata" not in document:
                document["storage_metadata"] = {}
            document["storage_metadata"]["updated_at"] = now
            document["storage_metadata"]["version"] = document["storage_metadata"].get("version", 1) + 1
        
        return document
    
    async def create_content_package(self, package: ContentPackage):
        """Create a content package"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")
        
        try:
            # Convert to dict and add metadata
            document = package.model_dump()
            document["partition_key"] = f"{package.subject}-{package.unit}"
            document = self._add_storage_metadata(document)
            document["document_type"] = "content_package"
            document["status"] = "generated"
            
            print(f"💾 Creating package: {package.id}")
            print(f"   📍 Partition Key: {document['partition_key']}")
            print(f"   📊 Document Size: ~{len(str(document))} characters")
            print(f"   🏷️  Status: {document['status']}")
            
            response = self.container.create_item(body=document)
            
            print(f"   ✅ Package created with storage metadata:")
            print(f"      📅 Created: {response['storage_metadata']['created_at']}")
            print(f"      🔢 Version: {response['storage_metadata']['version']}")
            
            return ContentPackage(**response)
            
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == 409:
                raise ValueError(f"Package {package.id} already exists")
            raise
    
    async def get_content_package(self, package_id: str, partition_key: str):
        """Get a content package"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")
        
        try:
            print(f"🔍 Retrieving package: {package_id}")
            print(f"   📍 Using partition key: {partition_key}")
            
            response = self.container.read_item(item=package_id, partition_key=partition_key)
            
            print(f"   ✅ Package found:")
            print(f"      📝 Subject: {response.get('subject')}")
            print(f"      📚 Unit: {response.get('unit')}")
            print(f"      🎯 Skill: {response.get('skill')}")
            print(f"      📅 Created: {response.get('storage_metadata', {}).get('created_at', 'N/A')}")
            print(f"      🏷️  Status: {response.get('status', 'N/A')}")
            
            return ContentPackage(**response)
        except exceptions.CosmosResourceNotFoundError:
            print(f"   ❌ Package not found: {package_id}")
            return None
    
    async def update_content_package(self, package: ContentPackage):
        """Update a content package"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")
        
        try:
            print(f"🔄 Updating package: {package.id}")
            print(f"   📝 New skill: {package.skill}")
            
            document = package.model_dump()
            old_version = document.get("storage_metadata", {}).get("version", 1)
            document = self._add_storage_metadata(document, is_update=True)
            new_version = document["storage_metadata"]["version"]
            
            print(f"   🔢 Version: {old_version} → {new_version}")
            
            response = self.container.replace_item(item=package.id, body=document)
            
            print(f"   ✅ Package updated successfully")
            print(f"      📅 Updated: {response['storage_metadata']['updated_at']}")
            
            return ContentPackage(**response)
            
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError(f"Package {package.id} not found")
    
    async def delete_content_package(self, package_id: str, partition_key: str):
        """Delete a content package"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")
        
        try:
            print(f"🗑️  Deleting package: {package_id}")
            print(f"   📍 Partition key: {partition_key}")
            
            self.container.delete_item(item=package_id, partition_key=partition_key)
            
            print(f"   ✅ Package deleted successfully from Cosmos DB")
            return True
        except exceptions.CosmosResourceNotFoundError:
            print(f"   ❌ Package not found for deletion: {package_id}")
            return False
    
    async def list_content_packages(self, subject=None, limit=100):
        """List content packages"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")
        
        try:
            conditions = ["c.document_type = 'content_package'"]
            parameters = []
            
            if subject:
                conditions.append("c.subject = @subject")
                parameters.append({"name": "@subject", "value": subject})
            
            query = f"SELECT * FROM c WHERE {' AND '.join(conditions)} ORDER BY c.storage_metadata.created_at DESC"
            
            print(f"📋 Listing packages with query:")
            print(f"   🔍 Query: {query}")
            print(f"   📊 Parameters: {parameters}")
            print(f"   📏 Limit: {limit}")
            
            packages = []
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                max_item_count=limit,
                enable_cross_partition_query=True
            ))
            
            print(f"   📦 Raw items found: {len(items)}")
            
            for i, item in enumerate(items):
                packages.append(ContentPackage(**item))
                print(f"      {i+1}. {item['id']} ({item['subject']}/{item['unit']} - {item['skill']})")
            
            return packages
            
        except Exception as e:
            logger.error(f"List failed: {e}")
            raise
    
    async def update_package_status(self, package_id: str, partition_key: str, status: str):
        """Update package status"""
        print(f"🏷️  Updating status for package: {package_id}")
        print(f"   📍 Partition key: {partition_key}")
        print(f"   🔄 New status: {status}")
        
        package = await self.get_content_package(package_id, partition_key)
        if not package:
            print(f"   ❌ Package not found for status update")
            return False
        
        old_status = getattr(package, 'status', 'unknown')
        package_dict = package.model_dump()
        package_dict["status"] = status
        package_dict = self._add_storage_metadata(package_dict, is_update=True)
        
        print(f"   🏷️  Status change: {old_status} → {status}")
        
        self.container.replace_item(item=package_id, body=package_dict)
        
        print(f"   ✅ Status updated successfully")
        return True
    
    def close(self):
        """Close connection"""
        self.client = None
        print("🔌 Cosmos DB connection closed")


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


async def run_cosmos_tests():
    """Run all CRUD tests"""
    
    print("🧪 SIMPLIFIED COSMOS DB TEST SUITE")
    print("=" * 50)
    
    # Create service instance
    cosmos_service = DirectCosmosService()
    
    try:
        # Initialize
        print("\n1️⃣ Initializing Cosmos DB...")
        success = await cosmos_service.initialize()
        if not success:
            print("❌ Initialization failed")
            return False
        
        # Health check
        print("\n2️⃣ Health Check...")
        health = await cosmos_service.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Documents: {health.get('total_documents', 0)}")
        
        # Create test package
        print("\n3️⃣ Testing CREATE...")
        test_package = await create_test_package()
        created_package = await cosmos_service.create_content_package(test_package)
        print(f"✅ Created: {created_package.id}")
        
        # Read test
        print("\n4️⃣ Testing READ...")
        partition_key = f"{test_package.subject}-{test_package.unit}"
        retrieved = await cosmos_service.get_content_package(test_package.id, partition_key)
        print(f"✅ Retrieved: {retrieved.id}")
        
        # List test
        print("\n5️⃣ Testing LIST...")
        packages = await cosmos_service.list_content_packages(subject="Mathematics")
        print(f"✅ Found {len(packages)} packages")
        
        # Update test
        print("\n6️⃣ Testing UPDATE...")
        retrieved.skill = "Updated Linear Equations"
        updated = await cosmos_service.update_content_package(retrieved)
        print(f"✅ Updated: {updated.skill}")
        
        # Status update test
        print("\n7️⃣ Testing STATUS UPDATE...")
        status_updated = await cosmos_service.update_package_status(test_package.id, partition_key, "approved")
        print(f"✅ Status updated: {status_updated}")
        
        # Delete test
        print("\n8️⃣ Testing DELETE...")
        deleted = await cosmos_service.delete_content_package(test_package.id, partition_key)
        print(f"✅ Deleted: {deleted}")
        
        # Verify deletion
        verify_deleted = await cosmos_service.get_content_package(test_package.id, partition_key)
        print(f"✅ Deletion verified: {verify_deleted is None}")
        
        print("\n🎉 ALL TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
        
    finally:
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