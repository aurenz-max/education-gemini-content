# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application
    APP_NAME: str = "Educational Content Generation System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # Gemini AI Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_TEXT_MODEL: str = "gemini-2.0-flash-001"
    GEMINI_TTS_MODEL: str = "gemini-2.5-flash-preview-tts"
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_TIMEOUT: int = 120
    
    # Azure Cosmos DB Configuration
    COSMOS_DB_ENDPOINT: str = ""
    COSMOS_DB_KEY: str = ""
    COSMOS_DB_DATABASE_NAME: str = "educational_content"
    COSMOS_DB_CONTAINER_NAME: str = "content_packages"
    COSMOS_DB_THROUGHPUT: int = 400
    COSMOS_DB_PARTITION_KEY: str = "/partition_key"
    COSMOS_DB_MAX_RETRY_ATTEMPTS: int = 3
    COSMOS_DB_RETRY_DELAY_SECONDS: float = 1.0
    COSMOS_DB_REQUEST_TIMEOUT: int = 30
    COSMOS_DB_CONSISTENCY_LEVEL: str = "Session"
    
    COSMOS_DB_CONTAINERS: dict = {
        "content_packages": "ContentPackages",
        "active_reviews": "ActiveReviews"
    }
    
    # Azure Blob Storage Configuration
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_ACCOUNT_KEY: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = "audio-files"
    BLOB_STORAGE_MAX_RETRY_ATTEMPTS: int = 3
    BLOB_STORAGE_RETRY_DELAY_SECONDS: float = 1.0
    BLOB_STORAGE_REQUEST_TIMEOUT: int = 30
    BLOB_STORAGE_CACHE_CONTROL: str = "public, max-age=31536000"  # 1 year cache
    
    # Content Generation Settings
    DEFAULT_DIFFICULTY_LEVEL: str = "intermediate"
    MAX_CONCURRENT_GENERATIONS: int = 5
    GENERATION_TIMEOUT: int = 300
    
    # Audio Configuration
    ENABLE_TTS: bool = False  # NEW: Toggle for text-to-speech generation
    AUDIO_STORAGE_PATH: str = "generated_audio"  # Local path for temp storage
    AUDIO_FORMAT: str = "wav"
    DEFAULT_TEACHER_VOICE: str = "Zephyr"
    DEFAULT_STUDENT_VOICE: str = "Puck"
    TARGET_AUDIO_DURATION: int = 300
    AUDIO_CLEANUP_LOCAL_AFTER_UPLOAD: bool = True  # Clean local files after blob upload
    
    # Review Workflow Configuration
    DEFAULT_REVIEW_TIME_MINUTES: int = 15
    AUTO_APPROVAL_THRESHOLD: float = 0.85
    REVIEW_DUE_DAYS: int = 2
    MAX_REVIEW_ASSIGNMENTS: int = 10
    
    # File Storage
    MAX_AUDIO_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    AUDIO_CLEANUP_DAYS: int = 30
    SUPPORTED_AUDIO_FORMATS: List[str] = ["wav", "mp3", "m4a"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600
    
    # Monitoring and Logging
    ENABLE_METRICS: bool = True
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 5
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @property
    def cosmos_connection_string(self) -> str:
        return f"AccountEndpoint={self.COSMOS_DB_ENDPOINT};AccountKey={self.COSMOS_DB_KEY};"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def blob_storage_enabled(self) -> bool:
        """Check if blob storage is properly configured"""
        return bool(self.AZURE_STORAGE_CONNECTION_STRING and self.AZURE_STORAGE_CONTAINER_NAME)
    
    @property
    def tts_enabled(self) -> bool:
        """Check if TTS is enabled and properly configured"""
        return self.ENABLE_TTS and bool(self.GEMINI_API_KEY)
    
    def get_cors_origins(self) -> List[str]:
        if self.is_production:
            return [
                "https://your-production-domain.com",
                "https://your-staging-domain.com"
            ]
        else:
            return self.ALLOWED_ORIGINS
    
    def get_audio_blob_path(self, package_id: str, filename: str) -> str:
        """Generate blob path for audio files"""
        return f"audio/{package_id}/{filename}"
    
    def validate_audio_file_size(self, file_size: int) -> bool:
        """Validate audio file size"""
        return file_size <= self.MAX_AUDIO_FILE_SIZE
    
    def get_supported_audio_extensions(self) -> List[str]:
        """Get list of supported audio file extensions"""
        return [f".{fmt}" for fmt in self.SUPPORTED_AUDIO_FORMATS]


# Create global settings instance
settings = Settings()


# Validation (relaxed for development)
def validate_settings():
    """Validate critical configuration settings"""
    errors = []
    warnings = []
    
    # Only require credentials in production
    if not settings.is_development:
        if not settings.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")
        if not settings.COSMOS_DB_ENDPOINT:
            errors.append("COSMOS_DB_ENDPOINT is required")
        if not settings.COSMOS_DB_KEY:
            errors.append("COSMOS_DB_KEY is required")
        if not settings.AZURE_STORAGE_CONNECTION_STRING:
            errors.append("AZURE_STORAGE_CONNECTION_STRING is required")
    else:
        # Development warnings
        if not settings.GEMINI_API_KEY:
            warnings.append("GEMINI_API_KEY not configured")
        if not settings.COSMOS_DB_ENDPOINT:
            warnings.append("COSMOS_DB_ENDPOINT not configured")
        if not settings.COSMOS_DB_KEY:
            warnings.append("COSMOS_DB_KEY not configured")
        if not settings.AZURE_STORAGE_CONNECTION_STRING:
            warnings.append("AZURE_STORAGE_CONNECTION_STRING not configured - blob storage unavailable")
    
    # Always validate ranges
    if settings.AUTO_APPROVAL_THRESHOLD < 0 or settings.AUTO_APPROVAL_THRESHOLD > 1:
        errors.append("AUTO_APPROVAL_THRESHOLD must be between 0 and 1")
    
    if settings.MAX_CONCURRENT_GENERATIONS < 1:
        errors.append("MAX_CONCURRENT_GENERATIONS must be at least 1")
    
    if settings.MAX_AUDIO_FILE_SIZE < 1024 * 1024:  # 1MB minimum
        errors.append("MAX_AUDIO_FILE_SIZE must be at least 1MB")
    
    # Output results
    if errors:
        if settings.is_development:
            print(f"⚠️  Configuration errors (development mode): {', '.join(errors)}")
        else:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    if warnings and settings.is_development:
        print(f"ℹ️  Configuration warnings: {', '.join(warnings)}")
    
    # Success message
    if settings.is_development:
        storage_status = "Enabled" if settings.blob_storage_enabled else "Disabled"
        tts_status = "Enabled" if settings.tts_enabled else "Disabled"
        print(f"🔧 Configuration loaded successfully")
        print(f"   📊 Environment: {settings.ENVIRONMENT}")
        print(f"   🗄️  Database: {'Configured' if settings.COSMOS_DB_ENDPOINT else 'Not configured'}")
        print(f"   📁 Blob Storage: {storage_status}")
        print(f"   🤖 AI Service: {'Configured' if settings.GEMINI_API_KEY else 'Not configured'}")
        print(f"   🔊 TTS Service: {tts_status}")


# Validate on import
validate_settings()