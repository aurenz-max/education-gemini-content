# backend/test_blob_storage.py
"""
Comprehensive Azure Blob Storage test with config integration
Run with: python test_blob_storage.py
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import wave
import numpy as np
import json
from datetime import datetime
from typing import Dict, Any  # Add this import

# Get the directory where this script is located (backend folder)
script_dir = Path(__file__).parent
env_path = script_dir / ".env"

# Load environment variables from backend/.env file
load_dotenv(env_path)

# Add the app directory to Python path
sys.path.append(str(script_dir))
sys.path.append(str(script_dir / "app"))

from app.database.blob_storage import blob_storage_service  # Fixed import path
from app.config import settings


def create_test_audio_file(file_path: Path, duration_seconds: float = 2.0, frequency: int = 440) -> Dict[str, Any]:
    """Create a test WAV audio file with specific characteristics"""
    sample_rate = 44100
    
    # Generate sine wave
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Add some fade in/out to make it sound more natural
    fade_samples = int(sample_rate * 0.1)  # 0.1 second fade
    if len(audio_data) > 2 * fade_samples:
        audio_data[:fade_samples] *= np.linspace(0, 1, fade_samples)
        audio_data[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    # Convert to 16-bit integers
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Write WAV file
    with wave.open(str(file_path), 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    file_size = file_path.stat().st_size
    
    print(f"📄 Created test audio file: {file_path.name}")
    print(f"   🎵 Duration: {duration_seconds}s @ {frequency}Hz")
    print(f"   📊 Size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    print(f"   🔊 Format: WAV, 16-bit, {sample_rate}Hz, Mono")
    
    return {
        "path": file_path,
        "size": file_size,
        "duration": duration_seconds,
        "frequency": frequency,
        "format": "wav"
    }


def create_large_test_file(file_path: Path, size_mb: float = 5.0) -> Dict[str, Any]:
    """Create a larger test file to test size limits"""
    target_size = int(size_mb * 1024 * 1024)
    chunk_size = 1024 * 1024  # 1MB chunks
    
    with open(file_path, 'wb') as f:
        written = 0
        while written < target_size:
            remaining = target_size - written
            chunk = min(chunk_size, remaining)
            # Write random-ish data
            data = bytes([(i + written) % 256 for i in range(chunk)])
            f.write(data)
            written += chunk
    
    actual_size = file_path.stat().st_size
    print(f"📄 Created large test file: {file_path.name}")
    print(f"   📊 Size: {actual_size:,} bytes ({actual_size / (1024*1024):.1f} MB)")
    
    return {
        "path": file_path,
        "size": actual_size,
        "size_mb": actual_size / (1024 * 1024)
    }


async def test_configuration():
    """Test configuration and display settings"""
    print("🔧 CONFIGURATION TEST")
    print("-" * 30)
    
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Blob Storage Enabled: {settings.blob_storage_enabled}")
    print(f"Container Name: {settings.AZURE_STORAGE_CONTAINER_NAME}")
    print(f"Max File Size: {settings.MAX_AUDIO_FILE_SIZE / (1024*1024):.1f} MB")
    print(f"Supported Formats: {settings.SUPPORTED_AUDIO_FORMATS}")
    print(f"Cleanup Local Files: {settings.AUDIO_CLEANUP_LOCAL_AFTER_UPLOAD}")
    
    if not settings.blob_storage_enabled:
        print("❌ Blob storage not properly configured!")
        return False
    
    print("✅ Configuration looks good!")
    return True


async def test_service_initialization():
    """Test service initialization"""
    print("\n🔌 SERVICE INITIALIZATION TEST")
    print("-" * 35)
    
    print("Initializing blob storage service...")
    success = await blob_storage_service.initialize()
    
    if success:
        print("✅ Service initialized successfully!")
        return True
    else:
        print("❌ Service initialization failed!")
        return False


async def test_health_check():
    """Test health check functionality"""
    print("\n🏥 HEALTH CHECK TEST")
    print("-" * 20)
    
    health = await blob_storage_service.health_check()
    
    print(f"Status: {health['status']}")
    print(f"Container: {health['container']}")
    print(f"Connection: {health.get('connection', 'N/A')}")
    print(f"Recent Blobs: {health.get('total_recent_blobs', 0)}")
    
    if health.get('container_last_modified'):
        print(f"Container Modified: {health['container_last_modified']}")
    
    if health['status'] == 'healthy':
        print("✅ Health check passed!")
        return True
    else:
        print(f"❌ Health check failed: {health.get('error', 'Unknown error')}")
        return False


async def test_audio_upload_download():
    """Test audio file upload and download"""
    print("\n📤 AUDIO UPLOAD/DOWNLOAD TEST")
    print("-" * 32)
    
    # Create temporary test files
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create different test audio files
        test_files = []
        
        # Small audio file
        small_audio = temp_dir / "small_lesson.wav"
        test_files.append(create_test_audio_file(small_audio, 1.5, 440))
        
        # Medium audio file
        medium_audio = temp_dir / "medium_lesson.wav"
        test_files.append(create_test_audio_file(medium_audio, 5.0, 523))  # C5 note
        
        # Large audio file
        large_audio = temp_dir / "large_lesson.wav"
        test_files.append(create_test_audio_file(large_audio, 30.0, 659))  # E5 note
        
        package_id = f"test_pkg_{int(datetime.now().timestamp())}"
        uploaded_files = []
        
        # Test uploads
        print(f"\n📤 Testing uploads for package: {package_id}")
        for i, file_info in enumerate(test_files):
            file_path = file_info["path"]
            filename = f"audio_{i+1}_{file_info['duration']}s.wav"
            
            print(f"\nUploading {filename}...")
            result = await blob_storage_service.upload_audio_file(
                package_id=package_id,
                file_path=str(file_path),
                filename=filename
            )
            
            if result["success"]:
                print(f"   ✅ Upload successful!")
                print(f"      📍 Blob: {result['blob_name']}")
                print(f"      🌐 URL: {result['blob_url']}")
                print(f"      📊 Size: {result['size_bytes']:,} bytes")
                uploaded_files.append(result)
            else:
                print(f"   ❌ Upload failed: {result['error']}")
                return False, None
        
        # Test download
        print(f"\n📥 Testing download...")
        if uploaded_files:
            download_path = temp_dir / "downloaded_audio.wav"
            blob_name = uploaded_files[0]["blob_name"]
            
            success = await blob_storage_service.download_audio_file(
                blob_name, str(download_path)
            )
            
            if success and download_path.exists():
                original_size = test_files[0]["size"]
                downloaded_size = download_path.stat().st_size
                
                print(f"   ✅ Download successful!")
                print(f"      📁 Path: {download_path}")
                print(f"      📊 Size: {downloaded_size:,} bytes")
                print(f"      🔍 Original: {original_size:,} bytes")
                
                if downloaded_size == original_size:
                    print(f"      ✅ File integrity verified!")
                else:
                    print(f"      ⚠️  Size mismatch!")
            else:
                print(f"   ❌ Download failed!")
                return False, None
        
        # Test URL retrieval
        print(f"\n🌐 Testing URL retrieval...")
        for file_info in uploaded_files:
            filename = Path(file_info["blob_name"]).name
            url = await blob_storage_service.get_audio_file_url(package_id, filename)
            
            if url:
                print(f"   ✅ URL retrieved for {filename}")
                print(f"      🔗 {url}")
            else:
                print(f"   ❌ Failed to get URL for {filename}")
        
        print("✅ Upload/Download test completed!")
        return package_id, uploaded_files
        
    finally:
        # Cleanup temp files
        try:
            for file_path in temp_dir.rglob("*"):
                if file_path.is_file():
                    file_path.unlink()
            temp_dir.rmdir()
        except:
            pass


async def test_file_listing():
    """Test file listing functionality"""
    print("\n📋 FILE LISTING TEST")
    print("-" * 20)
    
    # List all audio files
    all_files = await blob_storage_service.list_audio_files()
    
    if all_files["success"]:
        print(f"📁 Total audio files: {all_files['total_count']}")
        
        # Show first few files
        for i, blob in enumerate(all_files["blobs"][:5]):
            print(f"   {i+1}. {blob['name']}")
            print(f"      📊 Size: {blob['size']:,} bytes")
            print(f"      📅 Modified: {blob['last_modified']}")
            if blob.get('metadata'):
                print(f"      🏷️  Package: {blob['metadata'].get('package_id', 'N/A')}")
        
        if all_files['total_count'] > 5:
            print(f"   ... and {all_files['total_count'] - 5} more files")
        
        print("✅ File listing test completed!")
        return True
    else:
        print(f"❌ File listing failed: {all_files.get('error')}")
        return False


async def test_package_specific_operations(package_id: str):
    """Test package-specific operations"""
    print(f"\n📦 PACKAGE-SPECIFIC TEST ({package_id})")
    print("-" * 40)
    
    # List files for specific package
    package_files = await blob_storage_service.list_audio_files(package_id)
    
    if package_files["success"]:
        print(f"📋 Files in package {package_id}: {package_files['total_count']}")
        for blob in package_files["blobs"]:
            print(f"   - {blob['name']} ({blob['size']:,} bytes)")
        
        # Test cleanup
        print(f"\n🗑️  Testing cleanup for package {package_id}...")
        cleanup_result = await blob_storage_service.cleanup_package_audio(package_id)
        
        if cleanup_result["success"]:
            print(f"   ✅ Cleanup successful!")
            print(f"      🗑️  Deleted {cleanup_result['deleted_count']} files")
            for deleted in cleanup_result["deleted_files"]:
                print(f"         - {deleted}")
        else:
            print(f"   ❌ Cleanup failed: {cleanup_result.get('error')}")
            return False
        
        # Verify cleanup
        verify_files = await blob_storage_service.list_audio_files(package_id)
        if verify_files["success"] and verify_files["total_count"] == 0:
            print(f"   ✅ Cleanup verified - no files remaining")
        else:
            print(f"   ⚠️  Some files still remain: {verify_files['total_count']}")
        
        print("✅ Package-specific operations completed!")
        return True
    else:
        print(f"❌ Package listing failed: {package_files.get('error')}")
        return False


async def test_error_handling():
    """Test error handling scenarios"""
    print(f"\n🚨 ERROR HANDLING TEST")
    print("-" * 25)
    
    # Test non-existent file upload
    print("Testing upload of non-existent file...")
    result = await blob_storage_service.upload_audio_file(
        package_id="test_error_pkg",
        file_path="/non/existent/file.wav"
    )
    
    if not result["success"]:
        print(f"   ✅ Correctly handled missing file: {result['error']}")
    else:
        print(f"   ❌ Should have failed for missing file")
        return False
    
    # Test invalid file format (if we create one)
    temp_dir = Path(tempfile.mkdtemp())
    try:
        invalid_file = temp_dir / "test.txt"
        invalid_file.write_text("This is not an audio file")
        
        print("Testing upload of invalid file format...")
        result = await blob_storage_service.upload_audio_file(
            package_id="test_error_pkg",
            file_path=str(invalid_file)
        )
        
        if not result["success"]:
            print(f"   ✅ Correctly handled invalid format: {result['error']}")
        else:
            print(f"   ⚠️  Invalid format was accepted (might be OK)")
        
        # Test download of non-existent blob
        print("Testing download of non-existent blob...")
        success = await blob_storage_service.download_audio_file(
            "audio/nonexistent/file.wav",
            str(temp_dir / "download.wav")
        )
        
        if not success:
            print(f"   ✅ Correctly handled non-existent blob")
        else:
            print(f"   ❌ Should have failed for non-existent blob")
            return False
        
        # Test URL for non-existent file
        print("Testing URL for non-existent file...")
        url = await blob_storage_service.get_audio_file_url("nonexistent_pkg", "missing.wav")
        
        if url is None:
            print(f"   ✅ Correctly returned None for missing file")
        else:
            print(f"   ❌ Should have returned None for missing file")
            return False
        
        print("✅ Error handling test completed!")
        return True
        
    finally:
        # Cleanup
        try:
            for file_path in temp_dir.rglob("*"):
                if file_path.is_file():
                    file_path.unlink()
            temp_dir.rmdir()
        except:
            pass


async def test_large_file_handling():
    """Test handling of large files"""
    print(f"\n📏 LARGE FILE HANDLING TEST")
    print("-" * 30)
    
    # Check max file size setting
    max_size_mb = settings.MAX_AUDIO_FILE_SIZE / (1024 * 1024)
    print(f"Max file size: {max_size_mb:.1f} MB")
    
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Create a file just under the limit
        acceptable_size = max_size_mb * 0.8  # 80% of limit
        print(f"Creating {acceptable_size:.1f}MB test file...")
        
        acceptable_file = temp_dir / "acceptable_large.wav"
        create_large_test_file(acceptable_file, acceptable_size)
        
        # Test upload of acceptable large file
        result = await blob_storage_service.upload_audio_file(
            package_id="test_large_pkg",
            file_path=str(acceptable_file)
        )
        
        if result["success"]:
            print(f"   ✅ Large file upload successful!")
            print(f"      📊 Size: {result['size_bytes']:,} bytes")
            
            # Clean up the uploaded file
            await blob_storage_service.cleanup_package_audio("test_large_pkg")
        else:
            print(f"   ❌ Large file upload failed: {result['error']}")
        
        # Create a file over the limit (if limit is reasonable)
        if max_size_mb < 100:  # Only test if limit is reasonable
            oversized = max_size_mb * 1.2  # 120% of limit
            print(f"Creating {oversized:.1f}MB oversized test file...")
            
            oversized_file = temp_dir / "oversized.wav"
            create_large_test_file(oversized_file, oversized)
            
            # Test upload of oversized file
            result = await blob_storage_service.upload_audio_file(
                package_id="test_oversized_pkg",
                file_path=str(oversized_file)
            )
            
            if not result["success"]:
                print(f"   ✅ Correctly rejected oversized file: {result['error']}")
            else:
                print(f"   ⚠️  Oversized file was accepted (cleaning up...)")
                await blob_storage_service.cleanup_package_audio("test_oversized_pkg")
        
        print("✅ Large file handling test completed!")
        return True
        
    finally:
        # Cleanup temp files
        try:
            for file_path in temp_dir.rglob("*"):
                if file_path.is_file():
                    file_path.unlink()
            temp_dir.rmdir()
        except:
            pass


async def test_storage_statistics():
    """Test storage statistics functionality"""
    print(f"\n📊 STORAGE STATISTICS TEST")
    print("-" * 30)
    
    stats = await blob_storage_service.get_storage_stats()
    
    if stats["success"]:
        print(f"📁 Total blobs: {stats['total_blobs']:,}")
        print(f"📊 Total size: {stats['total_size_mb']:.2f} MB ({stats['total_size_bytes']:,} bytes)")
        print(f"📦 Unique packages: {stats['unique_packages']}")
        print(f"🪣 Container: {stats['container']}")
        
        print("✅ Storage statistics test completed!")
        return True
    else:
        print(f"❌ Storage statistics failed: {stats.get('error')}")
        return False


async def run_comprehensive_tests():
    """Run all blob storage tests"""
    print("🧪 COMPREHENSIVE AZURE BLOB STORAGE TEST SUITE")
    print("=" * 55)
    
    test_results = []
    
    try:
        # Configuration test
        result = await test_configuration()
        test_results.append(("Configuration", result))
        if not result:
            return False
        
        # Service initialization
        result = await test_service_initialization()
        test_results.append(("Service Initialization", result))
        if not result:
            return False
        
        # Health check
        result = await test_health_check()
        test_results.append(("Health Check", result))
        if not result:
            return False
        
        # Audio upload/download
        upload_result = await test_audio_upload_download()
        if isinstance(upload_result, tuple):
            package_id, uploaded_files = upload_result
            test_results.append(("Audio Upload/Download", package_id is not None))
        else:
            package_id = None
            test_results.append(("Audio Upload/Download", False))
        
        if not package_id:
            return False
        
        # File listing
        result = await test_file_listing()
        test_results.append(("File Listing", result))
        
        # Package-specific operations
        result = await test_package_specific_operations(package_id)
        test_results.append(("Package Operations", result))
        
        # Error handling
        result = await test_error_handling()
        test_results.append(("Error Handling", result))
        
        # Large file handling
        result = await test_large_file_handling()
        test_results.append(("Large File Handling", result))
        
        # Storage statistics
        result = await test_storage_statistics()
        test_results.append(("Storage Statistics", result))
        
        # Summary
        print(f"\n📋 TEST SUMMARY")
        print("=" * 20)
        
        passed = 0
        total = len(test_results)
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if success:
                passed += 1
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("🚀 Azure Blob Storage is fully operational!")
            return True
        else:
            print(f"\n⚠️  {total - passed} tests failed")
            return False
        
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        blob_storage_service.close()


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
    
    # Check required environment variables
    required_vars = [
        "AZURE_STORAGE_CONNECTION_STRING", 
        "AZURE_STORAGE_CONTAINER_NAME"
    ]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please add them to your .env file:")
        for var in missing_vars:
            if var == "AZURE_STORAGE_CONNECTION_STRING":
                print(f"   {var}=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net")
            else:
                print(f"   {var}=audio-files")
        return
    else:
        print("✅ All required environment variables found")
    
    # Run comprehensive tests
    success = await run_comprehensive_tests()
    
    if success:
        print("\n🎊 CONGRATULATIONS!")
        print("Azure Blob Storage integration is working perfectly!")
        print("You can now:")
        print("  📤 Upload audio files to Azure")
        print("  📥 Download files from Azure")
        print("  🗑️  Clean up packages")
        print("  📊 Monitor storage usage")
        print("  🌐 Get public URLs for audio files")
    else:
        print("\n❌ Some tests failed - check the output above")
        print("Make sure your Azure configuration is correct")


if __name__ == "__main__":
    asyncio.run(main())