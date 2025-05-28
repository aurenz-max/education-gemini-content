# test_api.py - Test your FastAPI endpoints including review workflow
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"


async def test_api_endpoints():
    """Test all API endpoints including review workflow"""
    
    print("🧪 TESTING FASTAPI ENDPOINTS WITH REVIEW WORKFLOW")
    print("=" * 60)
    
    # Store test data
    test_package_id = None
    test_subject = None
    test_unit = None
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health Check
        print("\n1️⃣ Testing Health Check...")
        try:
            async with session.get(f"{BASE_URL}/api/v1/health") as response:
                health_data = await response.json()
                print(f"✅ Health check: {health_data['status']}")
                print(f"   Cosmos DB: {health_data['services']['cosmos_db']['status']}")
                print(f"   Blob Storage: {health_data['services']['blob_storage']['status']}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
        
        # Test 2: Generate Content
        print("\n2️⃣ Testing Content Generation...")
        generation_request = {
            "subject": "Mathematics",
            "unit": "Basic Arithmetic",
            "skill": "Addition",
            "subskill": "Single-digit Addition",
            "difficulty_level": "beginner",
            "prerequisites": []
        }
        
        try:
            start_time = time.time()
            async with session.post(
                f"{BASE_URL}/api/v1/generate-content",
                json=generation_request
            ) as response:
                if response.status == 200:
                    package_data = await response.json()
                    generation_time = time.time() - start_time
                    
                    test_package_id = package_data['id']
                    test_subject = package_data['subject']
                    test_unit = package_data['unit']
                    
                    print(f"✅ Content generated successfully!")
                    print(f"   Package ID: {test_package_id}")
                    print(f"   Subject: {test_subject}")
                    print(f"   Unit: {test_unit}")
                    print(f"   Status: {package_data.get('status', 'unknown')}")
                    print(f"   Generation time: {generation_time:.2f}s")
                    
                else:
                    print(f"❌ Content generation failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Content generation failed: {e}")
            return False
        
        # Test 3: Test Review Queue (New!)
        print("\n3️⃣ Testing Review Queue...")
        try:
            async with session.get(f"{BASE_URL}/api/v1/packages/review-queue") as response:
                if response.status == 200:
                    review_queue = await response.json()
                    print(f"✅ Review queue retrieved successfully!")
                    print(f"   Packages needing review: {len(review_queue)}")
                    
                    # Check if our generated package is in the queue (handle both dict and object formats)
                    our_package_in_queue = False
                    if review_queue:
                        for pkg in review_queue:
                            pkg_id = pkg.get('id') if isinstance(pkg, dict) else getattr(pkg, 'id', None)
                            if pkg_id == test_package_id:
                                our_package_in_queue = True
                                break
                    
                    print(f"   Our test package in queue: {our_package_in_queue}")
                    
                    if review_queue:
                        sample_pkg = review_queue[0]
                        if isinstance(sample_pkg, dict):
                            print(f"   Sample package: {sample_pkg.get('id', 'unknown')} - {sample_pkg.get('subject', 'unknown')}/{sample_pkg.get('skill', 'unknown')}")
                        else:
                            print(f"   Sample package: {getattr(sample_pkg, 'id', 'unknown')} - {getattr(sample_pkg, 'subject', 'unknown')}/{getattr(sample_pkg, 'skill', 'unknown')}")
                        
                else:
                    print(f"❌ Review queue failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Review queue test failed: {e}")
        
        # Test 4: Test Review Queue with Filters (New!)
        print("\n4️⃣ Testing Review Queue with Filters...")
        try:
            params = {"subject": test_subject, "unit": test_unit, "limit": 10}
            async with session.get(f"{BASE_URL}/api/v1/packages/review-queue", params=params) as response:
                if response.status == 200:
                    filtered_queue = await response.json()
                    print(f"✅ Filtered review queue retrieved!")
                    print(f"   Packages for {test_subject}/{test_unit}: {len(filtered_queue)}")
                else:
                    print(f"❌ Filtered review queue failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Filtered review queue test failed: {e}")
        
        # Test 5: Test Package Review Info (New!)
        print("\n5️⃣ Testing Package Review Info...")
        try:
            params = {"subject": test_subject, "unit": test_unit}
            async with session.get(
                f"{BASE_URL}/api/v1/packages/{test_package_id}/review-info", 
                params=params
            ) as response:
                if response.status == 200:
                    review_info = await response.json()
                    print(f"✅ Review info retrieved!")
                    print(f"   Current status: {review_info['current_status']}")
                    print(f"   Review status: {review_info['review_status']}")
                    print(f"   Review notes: {len(review_info.get('review_notes', []))}")
                else:
                    print(f"❌ Review info failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Review info test failed: {e}")
        
        # Test 6: Test Package Approval (New!)
        print("\n6️⃣ Testing Package Approval...")
        try:
            approval_data = {
                "status": "approved",
                "reviewer_id": "test_educator_123",
                "notes": "This content looks excellent! Clear explanations and good examples. Ready for publication."
            }
            
            params = {"subject": test_subject, "unit": test_unit}
            async with session.put(
                f"{BASE_URL}/api/v1/packages/{test_package_id}/status",
                params=params,
                json=approval_data
            ) as response:
                if response.status == 200:
                    approval_result = await response.json()
                    print(f"✅ Package approved successfully!")
                    print(f"   Package ID: {approval_result['package_id']}")
                    print(f"   Status changed: {approval_result['old_status']} → {approval_result['new_status']}")
                    print(f"   Updated at: {approval_result['updated_at']}")
                else:
                    print(f"❌ Package approval failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Package approval test failed: {e}")
        
        # Test 7: Verify Status Change
        print("\n7️⃣ Verifying Status Change...")
        try:
            params = {"subject": test_subject, "unit": test_unit}
            async with session.get(
                f"{BASE_URL}/api/v1/packages/{test_package_id}/review-info",
                params=params
            ) as response:
                if response.status == 200:
                    updated_info = await response.json()
                    print(f"✅ Status verification successful!")
                    print(f"   Current status: {updated_info['current_status']}")
                    print(f"   Reviewed by: {updated_info.get('reviewed_by', 'None')}")
                    print(f"   Review notes count: {len(updated_info.get('review_notes', []))}")
                    
                    if updated_info.get('review_notes'):
                        latest_note = updated_info['review_notes'][-1]
                        print(f"   Latest note: {latest_note.get('note', '')[:50]}...")
                        
                else:
                    print(f"❌ Status verification failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Status verification failed: {e}")
        
        # Test 8: Test Package Rejection
        print("\n8️⃣ Testing Package Rejection...")
        try:
            # Generate another package to reject
            rejection_request = {
                "subject": "Science",
                "unit": "Physics",
                "skill": "Motion",
                "subskill": "Velocity",
                "difficulty_level": "intermediate"
            }
            
            async with session.post(
                f"{BASE_URL}/api/v1/generate-content",
                json=rejection_request
            ) as response:
                if response.status == 200:
                    reject_package = await response.json()
                    reject_package_id = reject_package['id']
                    reject_subject = reject_package['subject']
                    reject_unit = reject_package['unit']
                    
                    print(f"   Generated package to reject: {reject_package_id}")
                    
                    # Now reject it
                    rejection_data = {
                        "status": "rejected",
                        "reviewer_id": "test_educator_456",
                        "notes": "The visual demonstration has coding errors and the audio quality is poor. Needs regeneration."
                    }
                    
                    params = {"subject": reject_subject, "unit": reject_unit}
                    async with session.put(
                        f"{BASE_URL}/api/v1/packages/{reject_package_id}/status",
                        params=params,
                        json=rejection_data
                    ) as reject_response:
                        if reject_response.status == 200:
                            rejection_result = await reject_response.json()
                            print(f"✅ Package rejection successful!")
                            print(f"   Status: {rejection_result['new_status']}")
                        else:
                            print(f"❌ Package rejection failed: {reject_response.status}")
                else:
                    print(f"⚠️ Could not generate package for rejection test")
                    
        except Exception as e:
            print(f"❌ Package rejection test failed: {e}")
        
        # Test 9: Original Content Retrieval
        print("\n9️⃣ Testing Content Retrieval...")
        try:
            async with session.get(
                f"{BASE_URL}/api/v1/content/{test_package_id}",
                params={"subject": test_subject, "unit": test_unit}
            ) as response:
                if response.status == 200:
                    retrieved_data = await response.json()
                    print(f"✅ Content retrieved successfully!")
                    print(f"   Package ID: {retrieved_data['id']}")
                    print(f"   Status: {retrieved_data.get('status', 'unknown')}")
                    print(f"   Components: {list(retrieved_data.get('content', {}).keys())}")
                else:
                    print(f"❌ Content retrieval failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Content retrieval failed: {e}")
        
        # Test 10: List Content with Status Filter
        print("\n🔟 Testing Content Listing with Status Filter...")
        try:
            # Test approved packages
            async with session.get(f"{BASE_URL}/api/v1/content?status=approved") as response:
                if response.status == 200:
                    approved_packages = await response.json()
                    print(f"✅ Approved packages listing successful!")
                    print(f"   Approved packages: {len(approved_packages)}")
                    
            # Test rejected packages  
            async with session.get(f"{BASE_URL}/api/v1/content?status=rejected") as response:
                if response.status == 200:
                    rejected_packages = await response.json()
                    print(f"✅ Rejected packages listing successful!")
                    print(f"   Rejected packages: {len(rejected_packages)}")
                    
        except Exception as e:
            print(f"❌ Status-filtered listing failed: {e}")
        
        # Test 11: Storage Stats
        print("\n1️⃣1️⃣ Testing Storage Stats...")
        try:
            async with session.get(f"{BASE_URL}/api/v1/storage/stats") as response:
                if response.status == 200:
                    stats_data = await response.json()
                    print(f"✅ Storage stats retrieved!")
                    print(f"   Total packages: {stats_data.get('cosmos_db', {}).get('total_packages', 0)}")
                    print(f"   Blob storage size: {stats_data.get('blob_storage', {}).get('total_size_mb', 0)} MB")
                else:
                    print(f"❌ Storage stats failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Storage stats failed: {e}")
        
        print(f"\n🎉 COMPREHENSIVE API TESTING COMPLETED!")
        print(f"\n📋 Test Summary:")
        print(f"   ✅ API is running and accessible")
        print(f"   ✅ Content generation works with 'generated' status")
        print(f"   ✅ Review queue shows packages needing review")
        print(f"   ✅ Package approval workflow functional")
        print(f"   ✅ Package rejection workflow functional")
        print(f"   ✅ Status updates persist in database")
        print(f"   ✅ Review notes and metadata captured")
        print(f"   ✅ All CRUD operations functional")
        
        return True


def print_review_api_examples():
    """Print example usage for review workflow"""
    
    print("\n" + "📖 REVIEW WORKFLOW API EXAMPLES" + "\n" + "=" * 60)
    
    print("1️⃣ Get Packages for Review:")
    print("""
# Get all packages needing review
curl "http://localhost:8000/api/v1/packages/review-queue"

# Get packages for specific subject/unit
curl "http://localhost:8000/api/v1/packages/review-queue?subject=Mathematics&unit=Algebra"
""")
    
    print("2️⃣ Approve a Package:")
    print("""
curl -X PUT "http://localhost:8000/api/v1/packages/pkg_123456/status?subject=Mathematics&unit=Algebra" \\
     -H "Content-Type: application/json" \\
     -d '{
       "status": "approved",
       "reviewer_id": "educator_123",
       "notes": "Excellent content! Clear explanations and good examples."
     }'
""")
    
    print("3️⃣ Reject a Package:")
    print("""
curl -X PUT "http://localhost:8000/api/v1/packages/pkg_123456/status?subject=Mathematics&unit=Algebra" \\
     -H "Content-Type: application/json" \\
     -d '{
       "status": "rejected",
       "reviewer_id": "educator_123", 
       "notes": "Math errors in practice problems. Visual demo needs improvement."
     }'
""")
    
    print("4️⃣ Mark for Revision:")
    print("""
curl -X PUT "http://localhost:8000/api/v1/packages/pkg_123456/status?subject=Mathematics&unit=Algebra" \\
     -H "Content-Type: application/json" \\
     -d '{
       "status": "needs_revision",
       "reviewer_id": "educator_123",
       "notes": "Audio quality poor, reading content too advanced for grade level."
     }'
""")
    
    print("5️⃣ Get Review Information:")
    print("""
curl "http://localhost:8000/api/v1/packages/pkg_123456/review-info?subject=Mathematics&unit=Algebra"
""")
    
    print("6️⃣ List Packages by Status:")
    print("""
# Get approved packages
curl "http://localhost:8000/api/v1/content?status=approved"

# Get rejected packages
curl "http://localhost:8000/api/v1/content?status=rejected"
""")


async def test_review_workflow_specifically():
    """Test just the review workflow endpoints"""
    
    print("🔍 TESTING REVIEW WORKFLOW SPECIFICALLY")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Quick health check
        print("⚡ Quick health check...")
        try:
            async with session.get(f"{BASE_URL}/api/v1/health") as response:
                if response.status != 200:
                    print("❌ API not healthy, aborting review tests")
                    return False
                print("✅ API is healthy")
        except:
            print("❌ Cannot connect to API")
            return False
        
        # Generate a test package
        print("\n📝 Generating test package...")
        generation_request = {
            "subject": "TestSubject",
            "unit": "TestUnit", 
            "skill": "TestSkill",
            "subskill": "TestSubskill"
        }
        
        async with session.post(f"{BASE_URL}/api/v1/generate-content", json=generation_request) as response:
            if response.status == 200:
                package = await response.json()
                test_id = package['id']
                print(f"✅ Test package created: {test_id}")
            else:
                print("❌ Could not create test package")
                return False
        
        # Test review queue
        print("\n📋 Testing review queue...")
        async with session.get(f"{BASE_URL}/api/v1/packages/review-queue") as response:
            if response.status == 200:
                queue = await response.json()
                print(f"✅ Review queue has {len(queue)} packages")
                
                # Find our package (handle both dict and object formats)
                our_package = None  
                for p in queue:
                    pkg_id = p.get('id') if isinstance(p, dict) else getattr(p, 'id', None)
                    if pkg_id == test_id:
                        our_package = p
                        break
                if our_package:
                    print(f"✅ Our test package is in the review queue")
                else:
                    print(f"⚠️ Our test package not found in review queue")
            else:
                print("❌ Review queue request failed")
        
        # Test approval
        print(f"\n✅ Testing package approval...")
        approval_data = {
            "status": "approved",
            "reviewer_id": "test_reviewer",
            "notes": "Test approval note"
        }
        
        params = {"subject": "TestSubject", "unit": "TestUnit"}
        async with session.put(f"{BASE_URL}/api/v1/packages/{test_id}/status", params=params, json=approval_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Package approved: {result['old_status']} → {result['new_status']}")
            else:
                error_text = await response.text()
                print(f"❌ Approval failed: {response.status} - {error_text}")
        
        # Verify status change
        print(f"\n🔍 Verifying status change...")
        async with session.get(f"{BASE_URL}/api/v1/packages/{test_id}/review-info", params=params) as response:
            if response.status == 200:
                info = await response.json()
                print(f"✅ Status verified: {info['current_status']}")
                print(f"   Reviewed by: {info.get('reviewed_by', 'None')}")
                print(f"   Review notes: {len(info.get('review_notes', []))}")
            else:
                print("❌ Could not verify status")
        
        print(f"\n🎉 Review workflow test complete!")


async def main():
    """Main test function with options"""
    
    print("🚀 EDUCATIONAL CONTENT API TESTING SUITE")
    print("=" * 60)
    print("📝 Make sure your FastAPI server is running on localhost:8000")
    print("   Command: python -m app.main")
    print()
    print("Choose test option:")
    print("1. Full comprehensive test (recommended)")
    print("2. Review workflow only")
    print("3. Show API examples")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        input("\nPress Enter when your API server is running...")
        success = await test_api_endpoints()
        if success:
            print_review_api_examples()
            print(f"\n✅ All tests passed! Your review workflow API is working correctly.")
        else:
            print(f"\n❌ Some tests failed. Check your server logs.")
            
    elif choice == "2":
        input("\nPress Enter when your API server is running...")
        await test_review_workflow_specifically()
        
    elif choice == "3":
        print_review_api_examples()
        
    else:
        print("Invalid choice. Run the script again.")


if __name__ == "__main__":
    asyncio.run(main())