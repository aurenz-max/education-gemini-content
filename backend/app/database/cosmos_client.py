# backend/app/database/cosmos_client.py
import asyncio
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from azure.cosmos import CosmosClient, PartitionKey, exceptions

from app.config import settings
from app.models.content import ContentPackage


logger = logging.getLogger(__name__)


class CosmosDBService:
    """Azure Cosmos DB service for educational content storage"""
    
    def __init__(self):
        self.client: Optional[CosmosClient] = None
        self.database = None
        self.container = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Cosmos DB connection and ensure database/container exist"""
        try:
            logger.info("Initializing Cosmos DB connection...")
            
            # Create client
            self.client = CosmosClient(
                settings.COSMOS_DB_ENDPOINT,
                settings.COSMOS_DB_KEY
            )
            
            # Create or get database
            self.database = self.client.create_database_if_not_exists(
                id=settings.COSMOS_DB_DATABASE_NAME
            )
            logger.info(f"Database '{settings.COSMOS_DB_DATABASE_NAME}' ready")
            
            # Create or get container
            self.container = self.database.create_container_if_not_exists(
                id=settings.COSMOS_DB_CONTAINER_NAME,
                partition_key=PartitionKey(path=settings.COSMOS_DB_PARTITION_KEY),
                offer_throughput=settings.COSMOS_DB_THROUGHPUT
            )
            logger.info(f"Container '{settings.COSMOS_DB_CONTAINER_NAME}' ready")
            
            self._initialized = True
            logger.info("Cosmos DB initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Cosmos DB initialization failed: {str(e)}")
            self._initialized = False
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Cosmos DB connection health"""
        if not self._initialized:
            return {
                "status": "unhealthy",
                "error": "Service not initialized",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        try:
            # Simple query to test connection
            query = "SELECT VALUE COUNT(1) FROM c"
            items = list(self.container.query_items(query, enable_cross_partition_query=True))
            
            count = items[0] if items else 0
            
            return {
                "status": "healthy",
                "total_documents": count,
                "database": settings.COSMOS_DB_DATABASE_NAME,
                "container": settings.COSMOS_DB_CONTAINER_NAME,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _ensure_initialized(self):
        """Ensure service is initialized before operations"""
        if not self._initialized:
            raise RuntimeError("CosmosDBService not initialized. Call initialize() first.")
    
    def _generate_content_hash(self, content: Dict[str, Any]) -> str:
        """Generate SHA256 hash of content for integrity checking"""
        import json
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _add_storage_metadata(self, document: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """Add storage metadata to document - UPDATED with revision support"""
        now = datetime.now(timezone.utc).isoformat()
        
        if not is_update:
            document["storage_metadata"] = {
                "created_at": now,
                "updated_at": now,
                "version": 1,
                "content_hash": self._generate_content_hash(document.get("content", {})),
                "revision_history": []  # Initialize empty revision history
            }
        else:
            # Update existing metadata
            if "storage_metadata" not in document:
                document["storage_metadata"] = {}
            
            document["storage_metadata"]["updated_at"] = now
            document["storage_metadata"]["version"] = document["storage_metadata"].get("version", 1) + 1
            document["storage_metadata"]["content_hash"] = self._generate_content_hash(document.get("content", {}))
            
            # Preserve revision history from document level or initialize if missing
            if "revision_history" in document:
                # Move revision history from document level to storage_metadata if needed
                document["storage_metadata"]["revision_history"] = document.get("revision_history", [])
            elif "revision_history" not in document["storage_metadata"]:
                document["storage_metadata"]["revision_history"] = []
        
        return document
    
    async def create_content_package(self, package: ContentPackage) -> ContentPackage:
        """Create a new content package"""
        self._ensure_initialized()
        
        try:
            # Convert to dict and add metadata - preserve exact structure
            document = package.model_dump(mode='json')
            
            # Don't add partition_key to document if it doesn't exist in original
            if "partition_key" not in document:
                document["partition_key"] = f"{package.subject}-{package.unit}"
            
            document = self._add_storage_metadata(document)
            document["document_type"] = "content_package"
            document["status"] = "generated"  # Initial status
            
            logger.info(f"Creating content package: {package.id}")
            
            # Retry logic for transient failures
            for attempt in range(settings.COSMOS_DB_MAX_RETRY_ATTEMPTS):
                try:
                    response = self.container.create_item(
                        body=document
                    )
                    logger.info(f"Content package created successfully: {package.id}")
                    
                    # Convert back to ContentPackage model
                    return ContentPackage(**response)
                    
                except exceptions.CosmosHttpResponseError as e:
                    if e.status_code == 409:  # Conflict - document already exists
                        raise ValueError(f"Content package with ID {package.id} already exists")
                    elif attempt < settings.COSMOS_DB_MAX_RETRY_ATTEMPTS - 1:
                        await asyncio.sleep(settings.COSMOS_DB_RETRY_DELAY_SECONDS * (2 ** attempt))
                        continue
                    else:
                        raise
                        
        except Exception as e:
            logger.error(f"Failed to create content package {package.id}: {str(e)}")
            raise
    
    async def get_content_package(self, package_id: str, partition_key: str) -> Optional[ContentPackage]:
        """Get a content package by ID"""
        self._ensure_initialized()
        
        try:
            logger.debug(f"Retrieving content package: {package_id}")
            
            response = self.container.read_item(
                item=package_id,
                partition_key=partition_key
            )
            
            return ContentPackage(**response)
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Content package not found: {package_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve content package {package_id}: {str(e)}")
            raise
    
    async def update_content_package(self, package: ContentPackage) -> ContentPackage:
        """Update an existing content package"""
        self._ensure_initialized()
        
        try:
            # Convert to dict and update metadata
            document = package.model_dump(mode='json')
            document = self._add_storage_metadata(document, is_update=True)
            
            logger.info(f"Updating content package: {package.id}")
            
            response = self.container.replace_item(
                item=package.id,
                body=document
            )
            
            logger.info(f"Content package updated successfully: {package.id}")
            return ContentPackage(**response)
            
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError(f"Content package {package.id} not found for update")
        except Exception as e:
            logger.error(f"Failed to update content package {package.id}: {str(e)}")
            raise
    
    async def delete_content_package(self, package_id: str, partition_key: str) -> bool:
        """Delete a content package"""
        self._ensure_initialized()
        
        try:
            logger.info(f"Deleting content package: {package_id}")
            
            self.container.delete_item(
                item=package_id,
                partition_key=partition_key
            )
            
            logger.info(f"Content package deleted successfully: {package_id}")
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Content package not found for deletion: {package_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete content package {package_id}: {str(e)}")
            raise
    
    async def list_content_packages(
        self, 
        subject: Optional[str] = None,
        unit: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[ContentPackage]:
        """List content packages with optional filtering"""
        self._ensure_initialized()
        
        try:
            # Build query
            conditions = ["c.document_type = 'content_package'"]
            parameters = []
            
            if subject:
                conditions.append("c.subject = @subject")
                parameters.append({"name": "@subject", "value": subject})
            
            if unit:
                conditions.append("c.unit = @unit")
                parameters.append({"name": "@unit", "value": unit})
            
            if status:
                conditions.append("c.status = @status")
                parameters.append({"name": "@status", "value": status})
            
            query = f"SELECT * FROM c WHERE {' AND '.join(conditions)} ORDER BY c.storage_metadata.created_at DESC"
            
            logger.debug(f"Executing query: {query}")
            
            packages = []
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                max_item_count=limit,
                enable_cross_partition_query=True
            ))
            
            for item in items:
                packages.append(ContentPackage(**item))
            
            logger.info(f"Retrieved {len(packages)} content packages")
            return packages
            
        except Exception as e:
            logger.error(f"Failed to list content packages: {str(e)}")
            raise
    
    async def update_package_status(self, package_id: str, partition_key: str, status: str) -> bool:
        """Update only the status of a content package"""
        self._ensure_initialized()
        
        try:
            # Get current package
            package = await self.get_content_package(package_id, partition_key)
            if not package:
                return False
            
            # Update status
            package_dict = package.model_dump()
            package_dict["status"] = status
            package_dict = self._add_storage_metadata(package_dict, is_update=True)
            
            logger.info(f"Updating package {package_id} status to: {status}")
            
            self.container.replace_item(
                item=package_id,
                body=package_dict
            )
            
            logger.info(f"Package status updated successfully: {package_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update package status {package_id}: {str(e)}")
            raise
    
    async def get_packages_by_subject_unit(self, subject: str, unit: str) -> List[ContentPackage]:
        """Get all packages for a specific subject and unit (optimized query)"""
        self._ensure_initialized()
        
        try:
            partition_key = f"{subject}-{unit}"
            
            query = """
            SELECT * FROM c 
            WHERE c.document_type = 'content_package' 
            AND c.partition_key = @partition_key
            ORDER BY c.storage_metadata.created_at DESC
            """
            
            parameters = [{"name": "@partition_key", "value": partition_key}]
            
            packages = []
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=False
            ))
            
            for item in items:
                packages.append(ContentPackage(**item))
            
            logger.info(f"Retrieved {len(packages)} packages for {subject}/{unit}")
            return packages
            
        except Exception as e:
            logger.error(f"Failed to get packages for {subject}/{unit}: {str(e)}")
            raise
    
    def close(self):
        """Close the Cosmos DB connection"""
        if self.client:
            # Note: The sync client doesn't have an explicit close method
            self.client = None
            logger.info("Cosmos DB connection closed")


# Global service instance
cosmos_service = CosmosDBService()