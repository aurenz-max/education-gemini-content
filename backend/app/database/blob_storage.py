# backend/app/services/blob_storage.py
import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
import mimetypes
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)


class BlobStorageService:
    """Azure Blob Storage service for audio file management"""
    
    def __init__(self):
        self.blob_service_client: Optional[BlobServiceClient] = None
        self.container_client: Optional[ContainerClient] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Blob Storage connection"""
        try:
            if not settings.AZURE_STORAGE_CONNECTION_STRING:
                logger.error("AZURE_STORAGE_CONNECTION_STRING not configured")
                return False
            
            logger.info("Initializing Azure Blob Storage connection...")
            logger.info(f"Container: {settings.AZURE_STORAGE_CONTAINER_NAME}")
            
            # Create blob service client
            self.blob_service_client = BlobServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
            
            # Get container client
            self.container_client = self.blob_service_client.get_container_client(
                container=settings.AZURE_STORAGE_CONTAINER_NAME
            )
            
            # Test connection by checking if container exists
            try:
                container_properties = self.container_client.get_container_properties()
                logger.info(f"Connected to container '{settings.AZURE_STORAGE_CONTAINER_NAME}'")
                logger.info(f"Container created: {container_properties.last_modified}")
            except ResourceNotFoundError:
                logger.error(f"Container '{settings.AZURE_STORAGE_CONTAINER_NAME}' not found")
                logger.error("Please create the container in Azure Portal or enable auto-creation")
                return False
            
            self._initialized = True
            logger.info("Blob Storage initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Blob Storage initialization failed: {str(e)}")
            self._initialized = False
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Blob Storage connection health"""
        if not self._initialized:
            return {
                "status": "unhealthy",
                "error": "Service not initialized",
                "container": settings.AZURE_STORAGE_CONTAINER_NAME,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        try:
            # Test connection by listing a few blobs (without max_results parameter)
            blob_iter = self.container_client.list_blobs()
            blob_list = []
            count = 0
            for blob in blob_iter:
                blob_list.append(blob)
                count += 1
                if count >= 5:  # Limit to 5 items manually
                    break
            
            # Get container properties
            container_props = self.container_client.get_container_properties()
            
            return {
                "status": "healthy",
                "container": settings.AZURE_STORAGE_CONTAINER_NAME,
                "total_recent_blobs": len(blob_list),
                "container_last_modified": container_props.last_modified.isoformat() if container_props.last_modified else None,
                "connection": "active",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Blob Storage health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "container": settings.AZURE_STORAGE_CONTAINER_NAME,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _ensure_initialized(self):
        """Ensure service is initialized before operations"""
        if not self._initialized:
            raise RuntimeError("BlobStorageService not initialized. Call initialize() first.")
    
    def _get_blob_name(self, package_id: str, filename: str) -> str:
        """Generate blob name for audio file using config"""
        return settings.get_audio_blob_path(package_id, filename)
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type for file"""
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            # Default based on supported formats
            extension = Path(filename).suffix.lower()
            if extension == '.wav':
                return 'audio/wav'
            elif extension == '.mp3':
                return 'audio/mpeg'
            elif extension == '.m4a':
                return 'audio/mp4'
            else:
                return 'application/octet-stream'
        return content_type
    
    def _validate_audio_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate audio file before upload"""
        errors = []
        
        # Check if file exists
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            return {"valid": False, "errors": errors}
        
        # Check file size
        file_size = file_path.stat().st_size
        if not settings.validate_audio_file_size(file_size):
            max_size_mb = settings.MAX_AUDIO_FILE_SIZE / (1024 * 1024)
            errors.append(f"File too large: {file_size} bytes (max: {max_size_mb}MB)")
        
        # Check file extension
        extension = file_path.suffix.lower()
        if extension not in settings.get_supported_audio_extensions():
            errors.append(f"Unsupported format: {extension} (supported: {settings.SUPPORTED_AUDIO_FORMATS})")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "file_size": file_size,
            "extension": extension
        }
    
    async def upload_audio_file(
        self, 
        package_id: str, 
        file_path: str, 
        filename: Optional[str] = None,
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """Upload audio file to blob storage"""
        self._ensure_initialized()
        
        try:
            file_path = Path(file_path)
            
            # Validate file
            validation = self._validate_audio_file(file_path)
            if not validation["valid"]:
                logger.error(f"Audio file validation failed: {validation['errors']}")
                return {
                    "success": False,
                    "error": f"File validation failed: {'; '.join(validation['errors'])}",
                    "blob_name": None,
                    "blob_url": None
                }
            
            # Use provided filename or extract from path
            blob_filename = filename or file_path.name
            blob_name = self._get_blob_name(package_id, blob_filename)
            content_type = self._get_content_type(blob_filename)
            
            logger.info(f"Uploading audio file: {file_path} -> {blob_name}")
            logger.info(f"Content type: {content_type}")
            logger.info(f"File size: {validation['file_size']:,} bytes")
            
            # Upload file with retry logic
            for attempt in range(settings.BLOB_STORAGE_MAX_RETRY_ATTEMPTS):
                try:
                    with open(file_path, "rb") as data:
                        blob_client = self.container_client.get_blob_client(blob_name)
                        
                        # Create ContentSettings object properly
                        from azure.storage.blob import ContentSettings
                        content_settings = ContentSettings(
                            content_type=content_type,
                            cache_control=settings.BLOB_STORAGE_CACHE_CONTROL
                        )
                        
                        upload_result = blob_client.upload_blob(
                            data, 
                            overwrite=overwrite,
                            content_settings=content_settings,
                            metadata={
                                'package_id': package_id,
                                'original_filename': blob_filename,
                                'upload_timestamp': datetime.now(timezone.utc).isoformat(),
                                'file_size': str(validation['file_size'])
                            }
                        )
                    break
                    
                except Exception as e:
                    if attempt < settings.BLOB_STORAGE_MAX_RETRY_ATTEMPTS - 1:
                        wait_time = settings.BLOB_STORAGE_RETRY_DELAY_SECONDS * (2 ** attempt)
                        logger.warning(f"Upload attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise
            
            # Get blob URL
            blob_url = blob_client.url
            
            logger.info(f"Audio file uploaded successfully")
            logger.info(f"Blob URL: {blob_url}")
            
            # Cleanup local file if configured
            if settings.AUDIO_CLEANUP_LOCAL_AFTER_UPLOAD:
                try:
                    file_path.unlink()
                    logger.info(f"Cleaned up local file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup local file {file_path}: {e}")
            
            return {
                "success": True,
                "blob_name": blob_name,
                "blob_url": blob_url,
                "filename": blob_filename,
                "content_type": content_type,
                "size_bytes": validation['file_size'],
                "package_id": package_id
            }
            
        except Exception as e:
            logger.error(f"Failed to upload audio file {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "blob_name": None,
                "blob_url": None
            }
    
    async def download_audio_file(self, blob_name: str, download_path: str) -> bool:
        """Download audio file from blob storage"""
        self._ensure_initialized()
        
        try:
            logger.info(f"Downloading audio file: {blob_name} -> {download_path}")
            
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Create directory if it doesn't exist
            download_path = Path(download_path)
            download_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(download_path, "wb") as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
            
            logger.info(f"Audio file downloaded successfully: {download_path}")
            return True
            
        except ResourceNotFoundError:
            logger.error(f"Blob not found: {blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to download audio file {blob_name}: {str(e)}")
            return False
    
    async def delete_audio_file(self, blob_name: str) -> bool:
        """Delete audio file from blob storage"""
        self._ensure_initialized()
        
        try:
            logger.info(f"Deleting audio file: {blob_name}")
            
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob(delete_snapshots="include")
            
            logger.info(f"Audio file deleted successfully: {blob_name}")
            return True
            
        except ResourceNotFoundError:
            logger.warning(f"Blob not found for deletion: {blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete audio file {blob_name}: {str(e)}")
            return False
    
    async def get_audio_file_url(self, package_id: str, filename: str) -> Optional[str]:
        """Get public URL for audio file"""
        self._ensure_initialized()
        
        try:
            blob_name = self._get_blob_name(package_id, filename)
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Check if blob exists
            if blob_client.exists():
                return blob_client.url
            else:
                logger.warning(f"Audio file not found: {blob_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get audio file URL: {str(e)}")
            return None
    
    async def list_audio_files(self, package_id: Optional[str] = None) -> Dict[str, Any]:
        """List audio files, optionally filtered by package_id"""
        self._ensure_initialized()
        
        try:
            prefix = f"audio/{package_id}/" if package_id else "audio/"
            
            logger.info(f"Listing audio files with prefix: {prefix}")
            
            blobs = []
            for blob in self.container_client.list_blobs(name_starts_with=prefix):
                # Get blob metadata - use get_blob_properties instead of separate call
                try:
                    blob_client = self.container_client.get_blob_client(blob.name)
                    properties = blob_client.get_blob_properties()
                    
                    blob_info = {
                        "name": blob.name,
                        "size": blob.size,
                        "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                        "content_type": blob.content_settings.content_type if blob.content_settings else None,
                        "url": blob_client.url,
                        "metadata": properties.metadata or {}
                    }
                    blobs.append(blob_info)
                except Exception as prop_error:
                    # If we can't get properties, still include basic info
                    logger.warning(f"Could not get properties for {blob.name}: {prop_error}")
                    blob_info = {
                        "name": blob.name,
                        "size": blob.size,
                        "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                        "content_type": blob.content_settings.content_type if blob.content_settings else None,
                        "url": f"{self.container_client.url}/{blob.name}",
                        "metadata": {}
                    }
                    blobs.append(blob_info)
            
            logger.info(f"Found {len(blobs)} audio files")
            
            return {
                "success": True,
                "blobs": blobs,
                "total_count": len(blobs),
                "prefix": prefix
            }
            
        except Exception as e:
            logger.error(f"Failed to list audio files: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "blobs": []
            }
    
    async def cleanup_package_audio(self, package_id: str) -> Dict[str, Any]:
        """Delete all audio files for a package"""
        self._ensure_initialized()
        
        try:
            prefix = f"audio/{package_id}/"
            logger.info(f"Cleaning up audio files for package: {package_id}")
            
            deleted_files = []
            errors = []
            
            for blob in self.container_client.list_blobs(name_starts_with=prefix):
                try:
                    blob_client = self.container_client.get_blob_client(blob.name)
                    blob_client.delete_blob(delete_snapshots="include")
                    deleted_files.append(blob.name)
                    logger.info(f"Deleted: {blob.name}")
                except Exception as e:
                    error_msg = f"Failed to delete {blob.name}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            logger.info(f"Cleanup completed. Deleted {len(deleted_files)} files, {len(errors)} errors")
            
            return {
                "success": len(errors) == 0,
                "deleted_files": deleted_files,
                "deleted_count": len(deleted_files),
                "errors": errors,
                "package_id": package_id
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup package audio {package_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "deleted_files": [],
                "package_id": package_id
            }
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        self._ensure_initialized()
        
        try:
            total_blobs = 0
            total_size = 0
            packages = set()
            
            for blob in self.container_client.list_blobs():
                total_blobs += 1
                total_size += blob.size
                
                # Extract package ID from blob name
                if blob.name.startswith("audio/"):
                    parts = blob.name.split("/")
                    if len(parts) >= 2:
                        packages.add(parts[1])
            
            return {
                "success": True,
                "total_blobs": total_blobs,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "unique_packages": len(packages),
                "container": settings.AZURE_STORAGE_CONTAINER_NAME
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def close(self):
        """Close blob storage connection"""
        if self.blob_service_client:
            # The sync client doesn't have an explicit close method
            self.blob_service_client = None
            self.container_client = None
            self._initialized = False
            logger.info("Blob Storage connection closed")


# Global service instance
blob_storage_service = BlobStorageService()