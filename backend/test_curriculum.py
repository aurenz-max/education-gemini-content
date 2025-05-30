# backend/test_curriculum.py
"""
Enhanced test script for curriculum endpoints with focus on learning paths and prerequisites
Run from: backend/
Data location: backend/curriculum/math_refactored-syllabus.csv
"""

import asyncio
import aiohttp
import json
import os
import io
from pathlib import Path
from typing import Dict, List, Any

# File paths relative to backend/ directory
CURRICULUM_CSV = "backend/curriculum/math_refactored-syllabus.csv"
LEARNING_PATHS_JSON = "backend/curriculum/learning_path_decision_tree.json" 
SUBSKILL_PATHS_JSON = "backend/curriculum/math-subskill-paths.json"

API_BASE_URL = "http://localhost:8000"

class CurriculumTester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = None
        self.sample_data = {
            "subskills": [],
            "skills": [],
            "subjects": [],
            "grades": []
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_api_health(self):
        """Check if API is running"""
        try:
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                if response.status == 200:
                    print("✅ API is running")
                    return True
                else:
                    print(f"⚠️ API health check returned: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ API is not accessible: {e}")
            print("Make sure your FastAPI server is running on http://localhost:8000")
            return False
    
    async def load_curriculum_data(self):
        """Load curriculum data from files"""
        print("\n📚 Loading curriculum data...")
        
        # Check if files exist
        files_to_check = [
            (CURRICULUM_CSV, "Curriculum CSV"),
            (LEARNING_PATHS_JSON, "Learning Paths JSON"),
            (SUBSKILL_PATHS_JSON, "Subskill Paths JSON")
        ]
        
        for file_path, description in files_to_check:
            if not os.path.exists(file_path):
                print(f"❌ Missing file: {file_path} ({description})")
                return False
            else:
                print(f"✅ Found: {file_path}")
        
        try:
            # Read files into memory first
            print("   📖 Reading file contents...")
            
            with open(CURRICULUM_CSV, 'rb') as f:
                csv_content = f.read()
            
            with open(LEARNING_PATHS_JSON, 'rb') as f:
                learning_paths_content = f.read()
            
            with open(SUBSKILL_PATHS_JSON, 'rb') as f:
                subskill_paths_content = f.read()
            
            print(f"   📊 File sizes: CSV={len(csv_content)} bytes, LP={len(learning_paths_content)} bytes, SP={len(subskill_paths_content)} bytes")
            
            # Create form data with file-like objects
            data = aiohttp.FormData()
            
            # Add curriculum CSV file
            data.add_field('curriculum_file',
                          io.BytesIO(csv_content),
                          filename='math_refactored-syllabus.csv',
                          content_type='text/csv')
            
            # Add learning paths JSON file  
            data.add_field('learning_paths_file',
                          io.BytesIO(learning_paths_content),
                          filename='learning_path_decision_tree.json',
                          content_type='application/json')
            
            # Add subskill paths JSON file
            data.add_field('subskill_paths_file',
                          io.BytesIO(subskill_paths_content),
                          filename='math-subskill-paths.json',
                          content_type='application/json')
            
            # Upload data
            print("   📤 Uploading to API...")
            url = f"{self.base_url}/api/v1/curriculum/load"
            
            async with self.session.post(url, data=data) as response:
                print(f"   📡 Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Curriculum loaded successfully!")
                    print(f"   📊 Records loaded: {result['curriculum_records']}")
                    print(f"   🗺️ Learning paths: {result['learning_paths']}")
                    print(f"   🔗 Subskill paths: {result['subskill_paths']}")
                    print(f"   📚 Subjects: {', '.join(result['subjects'])}")
                    
                    # Store subjects for later tests
                    self.sample_data["subjects"] = result['subjects']
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to load curriculum: {response.status}")
                    print(f"   Error: {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error loading curriculum: {e}")
            import traceback
            print(f"   📋 Full traceback:")
            traceback.print_exc()
            return False
    
    async def test_curriculum_status(self):
        """Test curriculum status endpoint and collect sample data"""
        print("\n📊 Testing curriculum status...")
        
        try:
            async with self.session.get(f"{self.base_url}/api/v1/curriculum/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Curriculum status retrieved")
                    print(f"   Loaded: {data['loaded']}")
                    
                    stats = data['statistics']
                    print(f"   📈 Statistics:")
                    print(f"     • Total units: {stats['total_units']}")
                    print(f"     • Total skills: {stats['total_skills']}")
                    print(f"     • Total subskills: {stats['total_subskills']}")
                    print(f"     • Learning paths: {stats['learning_paths']}")
                    print(f"     • Subskill paths: {stats['subskill_paths']}")
                    print(f"     • Subjects/Grades: {len(stats['subjects_grades'])}")
                    
                    # Show some sample data
                    print(f"   📋 Sample subskills: {data['sample_subskills'][:5]}...")
                    
                    # Store sample data for further testing
                    self.sample_data["subskills"] = data['sample_subskills']
                    return True, data['sample_subskills']
                else:
                    error_text = await response.text()
                    print(f"❌ Status check failed: {response.status}")
                    print(f"   Error: {error_text}")
                    return False, []
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            return False, []
    
    async def test_subjects_and_grades(self):
        """Test subjects and grades endpoints"""
        print("\n🏫 Testing subjects and grades endpoints...")
        
        try:
            # Test subjects endpoint
            async with self.session.get(f"{self.base_url}/api/v1/curriculum/subjects") as response:
                if response.status == 200:
                    data = await response.json()
                    subjects = data['subjects']
                    print(f"✅ Subjects endpoint: {len(subjects)} subjects found")
                    print(f"   📚 Available subjects: {', '.join(subjects)}")
                    
                    self.sample_data["subjects"] = subjects
                    
                    # Test grades endpoint (all grades)
                    async with self.session.get(f"{self.base_url}/api/v1/curriculum/grades") as grades_response:
                        if grades_response.status == 200:
                            grades_data = await grades_response.json()
                            all_grades = grades_data['grades']
                            print(f"✅ All grades endpoint: {len(all_grades)} grades found")
                            print(f"   🎓 Available grades: {', '.join(all_grades)}")
                            
                            self.sample_data["grades"] = all_grades
                            
                            # Test grades filtered by subject
                            if subjects:
                                test_subject = subjects[0]
                                async with self.session.get(
                                    f"{self.base_url}/api/v1/curriculum/grades?subject={test_subject}"
                                ) as filtered_response:
                                    if filtered_response.status == 200:
                                        filtered_data = await filtered_response.json()
                                        subject_grades = filtered_data['grades']
                                        print(f"✅ Grades for {test_subject}: {', '.join(subject_grades)}")
                                    else:
                                        print(f"❌ Filtered grades failed: {filtered_response.status}")
                            
                            return True
                        else:
                            print(f"❌ Grades endpoint failed: {grades_response.status}")
                            return False
                else:
                    print(f"❌ Subjects endpoint failed: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error testing subjects/grades: {e}")
            return False
    
    async def test_curriculum_browsing(self):
        """Test curriculum browsing with detailed structure inspection"""
        print("\n🔍 Testing curriculum browsing...")
        
        try:
            # Test getting all curricula
            async with self.session.get(f"{self.base_url}/api/v1/curriculum/browse") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Browse all curricula")
                    print(f"   📊 Total curricula: {data['total_curricula']}")
                    
                    if data['curricula']:
                        # Inspect first curriculum structure
                        first_curriculum = data['curricula'][0]
                        subject = first_curriculum['subject']
                        grade = first_curriculum['grade']
                        units = first_curriculum['units']
                        
                        print(f"   📖 Sample curriculum: {subject} - {grade}")
                        print(f"     • Units: {len(units)}")
                        
                        # Inspect first unit structure
                        if units:
                            first_unit = units[0]
                            skills = first_unit['skills']
                            print(f"     • First unit: {first_unit['unit_title']} ({len(skills)} skills)")
                            
                            # Inspect first skill structure
                            if skills:
                                first_skill = skills[0]
                                subskills = first_skill['subskills']
                                print(f"       • First skill: {first_skill['skill_description'][:50]}... ({len(subskills)} subskills)")
                                
                                # Store skill ID for learning path testing
                                self.sample_data["skills"].append(first_skill['skill_id'])
                                
                                # Show subskill structure
                                if subskills:
                                    sample_subskill = subskills[0]
                                    print(f"       • Sample subskill: {sample_subskill['subskill_id']}")
                                    print(f"         - Description: {sample_subskill['subskill_description'][:60]}...")
                                    print(f"         - Difficulty: {sample_subskill['target_difficulty']} (range: {sample_subskill['difficulty_start']}-{sample_subskill['difficulty_end']})")
                        
                        # Test filtering by subject and grade
                        print(f"\n   🔍 Testing filtered browse for {subject} - {grade}...")
                        async with self.session.get(
                            f"{self.base_url}/api/v1/curriculum/browse?subject={subject}&grade={grade}"
                        ) as filtered_response:
                            if filtered_response.status == 200:
                                filtered_data = await filtered_response.json()
                                print(f"   ✅ Filtered browse successful: {filtered_data['total_curricula']} results")
                                print(f"       Applied filters: Subject={filtered_data['filters']['subject']}, Grade={filtered_data['filters']['grade']}")
                            else:
                                print(f"   ❌ Filtered browse failed: {filtered_response.status}")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Browse failed: {response.status}")
                    print(f"   Error: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error browsing curriculum: {e}")
            return False
    
    async def test_subskill_context_detailed(self):
        """Test subskill context with detailed analysis of returned data"""
        print("\n🎯 Testing subskill context (detailed analysis)...")
        
        try:
            if not self.sample_data["subskills"]:
                print("❌ No sample subskills available")
                return False
            
            # Test multiple subskills to see variety in responses
            test_subskills = self.sample_data["subskills"][:3]  # Test first 3
            
            for i, subskill_id in enumerate(test_subskills):
                print(f"\n   📋 Testing subskill {i+1}: {subskill_id}")
                
                async with self.session.get(
                    f"{self.base_url}/api/v1/curriculum/context/{subskill_id}"
                ) as response:
                    if response.status == 200:
                        context = await response.json()
                        
                        print(f"   ✅ Context retrieved for {subskill_id}")
                        print(f"     📚 Subject: {context['subject']}")
                        print(f"     🎓 Grade: {context['grade']}")
                        print(f"     📖 Unit: {context['unit']}")
                        print(f"     🎯 Skill: {context['skill'][:60]}...")
                        print(f"     🔹 Subskill: {context['subskill'][:60]}...")
                        print(f"     📊 Difficulty Level: {context['difficulty_level']} (target: {context['target_difficulty']})")
                        print(f"     📈 Difficulty Range: {context['difficulty_range']['start']} - {context['difficulty_range']['end']}")
                        
                        # Prerequisites analysis
                        prereqs = context['prerequisites']
                        print(f"     📋 Prerequisites: {len(prereqs)} items")
                        if prereqs:
                            print(f"       • Sample prereqs: {prereqs[:3]}")
                        else:
                            print(f"       • No prerequisites found")
                        
                        # Learning path analysis
                        learning_path = context['learning_path']
                        print(f"     🗺️ Learning Path: {len(learning_path)} next skills")
                        if learning_path:
                            print(f"       • Next skills: {learning_path[:3]}")
                        
                        # Next subskill analysis
                        next_subskill = context['next_subskill']
                        if next_subskill:
                            print(f"     ➡️ Next Subskill: {next_subskill}")
                        else:
                            print(f"     ➡️ Next Subskill: None (end of path)")
                        
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Context failed for {subskill_id}: {response.status}")
                        print(f"     Error: {error_text}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing subskill context: {e}")
            return False
    
    async def test_learning_paths(self):
        """Test learning path endpoints"""
        print("\n🗺️ Testing learning path endpoints...")
        
        try:
            if not self.sample_data["skills"]:
                print("❌ No sample skills available for testing")
                return False
            
            success_count = 0
            test_skills = self.sample_data["skills"][:3]  # Test first 3 skills
            
            for skill_id in test_skills:
                print(f"\n   🎯 Testing learning path for skill: {skill_id}")
                
                async with self.session.get(
                    f"{self.base_url}/api/v1/curriculum/learning-path/{skill_id}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        next_skills = data['next_skills']
                        path_length = data['path_length']
                        
                        print(f"   ✅ Learning path retrieved")
                        print(f"     📏 Path length: {path_length}")
                        
                        if next_skills:
                            print(f"     ➡️ Next skills in path:")
                            for j, next_skill in enumerate(next_skills[:5]):  # Show max 5
                                print(f"       {j+1}. {next_skill}")
                            if len(next_skills) > 5:
                                print(f"       ... and {len(next_skills) - 5} more")
                        else:
                            print(f"     ➡️ No next skills found (terminal skill)")
                        
                        success_count += 1
                    else:
                        print(f"   ❌ Learning path failed: {response.status}")
            
            if success_count > 0:
                print(f"\n   📊 Learning path test summary: {success_count}/{len(test_skills)} successful")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error testing learning paths: {e}")
            return False
    
    async def test_subskill_paths(self):
        """Test subskill progression paths"""
        print("\n🔗 Testing subskill progression paths...")
        
        try:
            if not self.sample_data["subskills"]:
                print("❌ No sample subskills available")
                return False
            
            paths_with_next = 0
            paths_without_next = 0
            test_subskills = self.sample_data["subskills"][:5]  # Test first 5
            
            for subskill_id in test_subskills:
                print(f"\n   🔍 Testing subskill path: {subskill_id}")
                
                async with self.session.get(
                    f"{self.base_url}/api/v1/curriculum/subskill-path/{subskill_id}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        current = data['current_subskill']
                        next_subskill = data['next_subskill']
                        has_next = data['has_next']
                        
                        print(f"   ✅ Subskill path retrieved")
                        print(f"     📍 Current: {current}")
                        
                        if has_next:
                            print(f"     ➡️ Next subskill: {next_subskill}")
                            paths_with_next += 1
                        else:
                            print(f"     🏁 End of path (no next subskill)")
                            paths_without_next += 1
                    else:
                        print(f"   ❌ Subskill path failed: {response.status}")
            
            print(f"\n   📊 Subskill path summary:")
            print(f"     • With next subskill: {paths_with_next}")
            print(f"     • End of path: {paths_without_next}")
            print(f"     • Total tested: {len(test_subskills)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing subskill paths: {e}")
            return False
    
    async def test_prerequisites_analysis(self):
        """Analyze prerequisites across multiple subskills"""
        print("\n📋 Testing prerequisites analysis...")
        
        try:
            if not self.sample_data["subskills"]:
                print("❌ No sample subskills available")
                return False
            
            prereq_stats = {
                "subskills_with_prereqs": 0,
                "subskills_without_prereqs": 0,
                "total_prereqs": 0,
                "max_prereqs": 0,
                "sample_prereqs": set()
            }
            
            test_subskills = self.sample_data["subskills"][:10]  # Test first 10
            
            for subskill_id in test_subskills:
                async with self.session.get(
                    f"{self.base_url}/api/v1/curriculum/context/{subskill_id}"
                ) as response:
                    if response.status == 200:
                        context = await response.json()
                        prereqs = context['prerequisites']
                        
                        if prereqs:
                            prereq_stats["subskills_with_prereqs"] += 1
                            prereq_stats["total_prereqs"] += len(prereqs)
                            prereq_stats["max_prereqs"] = max(prereq_stats["max_prereqs"], len(prereqs))
                            prereq_stats["sample_prereqs"].update(prereqs[:3])  # Add sample prereqs
                        else:
                            prereq_stats["subskills_without_prereqs"] += 1
            
            print("   ✅ Prerequisites analysis complete")
            print(f"     📊 Statistics:")
            print(f"       • Subskills with prerequisites: {prereq_stats['subskills_with_prereqs']}")
            print(f"       • Subskills without prerequisites: {prereq_stats['subskills_without_prereqs']}")
            print(f"       • Total prerequisites found: {prereq_stats['total_prereqs']}")
            print(f"       • Max prerequisites per subskill: {prereq_stats['max_prereqs']}")
            
            if prereq_stats["sample_prereqs"]:
                sample_list = list(prereq_stats["sample_prereqs"])[:5]
                print(f"       • Sample prerequisite IDs: {sample_list}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error analyzing prerequisites: {e}")
            return False
    
    async def test_data_consistency(self):
        """Test data consistency across endpoints"""
        print("\n🔍 Testing data consistency...")
        
        try:
            consistency_checks = []
            
            # Check 1: Subject consistency
            subjects_from_subjects_endpoint = set(self.sample_data["subjects"])
            
            # Get subjects from browse endpoint
            async with self.session.get(f"{self.base_url}/api/v1/curriculum/browse") as response:
                if response.status == 200:
                    browse_data = await response.json()
                    subjects_from_browse = set(curriculum['subject'] for curriculum in browse_data['curricula'])
                    
                    subjects_match = subjects_from_subjects_endpoint == subjects_from_browse
                    consistency_checks.append(("Subject consistency", subjects_match))
                    
                    if subjects_match:
                        print("   ✅ Subject consistency: PASS")
                    else:
                        print("   ❌ Subject consistency: FAIL")
                        print(f"     Subjects endpoint: {subjects_from_subjects_endpoint}")
                        print(f"     Browse endpoint: {subjects_from_browse}")
            
            # Check 2: Grade consistency  
            grades_from_grades_endpoint = set(self.sample_data["grades"])
            grades_from_browse = set(curriculum['grade'] for curriculum in browse_data['curricula'])
            
            grades_match = grades_from_grades_endpoint == grades_from_browse
            consistency_checks.append(("Grade consistency", grades_match))
            
            if grades_match:
                print("   ✅ Grade consistency: PASS")
            else:
                print("   ❌ Grade consistency: FAIL")
            
            # Check 3: Subskill ID consistency
            if self.sample_data["subskills"]:
                test_subskill = self.sample_data["subskills"][0]
                
                async with self.session.get(
                    f"{self.base_url}/api/v1/curriculum/context/{test_subskill}"
                ) as response:
                    if response.status == 200:
                        context = await response.json()
                        context_subskill_id = context['subskill_id']
                        
                        id_match = test_subskill == context_subskill_id
                        consistency_checks.append(("Subskill ID consistency", id_match))
                        
                        if id_match:
                            print("   ✅ Subskill ID consistency: PASS")
                        else:
                            print("   ❌ Subskill ID consistency: FAIL")
            
            # Summary
            total_checks = len(consistency_checks)
            passed_checks = sum(1 for _, passed in consistency_checks if passed)
            
            print(f"\n   📊 Consistency check summary: {passed_checks}/{total_checks} passed")
            
            return passed_checks == total_checks
            
        except Exception as e:
            print(f"❌ Error testing data consistency: {e}")
            return False

async def main():
    """Run comprehensive curriculum endpoint tests"""
    print("🧪 Comprehensive Curriculum Endpoints Test Suite")
    print("=" * 60)
    
    async with CurriculumTester() as tester:
        # Phase 1: Basic setup
        if not await tester.check_api_health():
            return
        
        if not await tester.load_curriculum_data():
            return
        
        # Phase 2: Core endpoint tests
        print("\n" + "=" * 60)
        print("🔬 PHASE 2: CORE ENDPOINT TESTING")
        print("=" * 60)
        
        status_result, sample_subskills = await tester.test_curriculum_status()
        
        tests = [
            ("Subjects and Grades", tester.test_subjects_and_grades()),
            ("Curriculum Browsing", tester.test_curriculum_browsing()),
            ("Subskill Context (Detailed)", tester.test_subskill_context_detailed()),
        ]
        
        results = [status_result]
        
        for test_name, test_coro in tests:
            try:
                print(f"\n{'='*20} {test_name.upper()} {'='*20}")
                result = await test_coro
                results.append(result)
                if not result:
                    print(f"   ⚠️ {test_name} failed")
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append(False)
        
        # Phase 3: Learning paths and prerequisites
        print("\n" + "=" * 60)
        print("🗺️ PHASE 3: LEARNING PATHS & PREREQUISITES")
        print("=" * 60)
        
        learning_tests = [
            ("Learning Paths", tester.test_learning_paths()),
            ("Subskill Paths", tester.test_subskill_paths()),
            ("Prerequisites Analysis", tester.test_prerequisites_analysis()),
        ]
        
        for test_name, test_coro in learning_tests:
            try:
                print(f"\n{'='*15} {test_name.upper()} {'='*15}")
                result = await test_coro
                results.append(result)
                if not result:
                    print(f"   ⚠️ {test_name} failed")
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append(False)
        
        # Phase 4: Data consistency
        print("\n" + "=" * 60)
        print("🔍 PHASE 4: DATA CONSISTENCY CHECKS")
        print("=" * 60)
        
        try:
            consistency_result = await tester.test_data_consistency()
            results.append(consistency_result)
        except Exception as e:
            print(f"❌ Data consistency check failed: {e}")
            results.append(False)
        
        # Final summary
        print("\n" + "=" * 60)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if all(results):
            print("\n🎉 All tests passed! Curriculum system is working correctly.")
            print("   • Curriculum data loads properly")
            print("   • All endpoints return expected data structures")
            print("   • Learning paths and prerequisites are functional")
            print("   • Data consistency is maintained across endpoints")
        else:
            print("\n⚠️ Some tests failed. Key areas to investigate:")
            if not results[0]:
                print("   • Curriculum loading/status")
            if len(results) > 3 and not results[3]:
                print("   • Subskill context and prerequisites")
            if len(results) > 4 and not results[4]:
                print("   • Learning path functionality")
            print("   • Check the detailed output above for specific issues")

if __name__ == "__main__":
    # Check if running from correct directory
    if not os.path.exists("backend/curriculum"):
        print("❌ Error: Run this script from the project root directory")
        print("   Expected structure:")
        print("   .")
        print("   ├── test_curriculum.py  (this script)")
        print("   └── backend/")
        print("       └── curriculum/")
        print("           ├── math_refactored-syllabus.csv")
        print("           ├── learning_path_decision_tree.json")
        print("           └── math-subskill-paths.json")
        exit(1)
    
    asyncio.run(main())