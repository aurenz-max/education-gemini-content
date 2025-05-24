# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application
    APP_NAME: str = "Educational Content Generation System"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # Gemini AI Configuration
    GEMINI_API_KEY: str
    GEMINI_TEXT_MODEL: str = "gemini-2.0-flash-001"
    GEMINI_TTS_MODEL: str = "gemini-2.5-flash-preview-tts"
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_TIMEOUT: int = 120  # seconds
    
    # Azure Cosmos DB Configuration
    COSMOS_DB_ENDPOINT: str
    COSMOS_DB_KEY: str
    COSMOS_DB_DATABASE_NAME: str = "educational_content"
    COSMOS_DB_CONTAINERS: dict = {
        "content_packages": "ContentPackages",
        "active_reviews": "ActiveReviews"
    }
    
    # Content Generation Settings
    DEFAULT_DIFFICULTY_LEVEL: str = "intermediate"
    MAX_CONCURRENT_GENERATIONS: int = 5
    GENERATION_TIMEOUT: int = 300  # 5 minutes
    
    # Audio Configuration
    AUDIO_STORAGE_PATH: str = "generated_audio"
    AUDIO_FORMAT: str = "wav"
    DEFAULT_TEACHER_VOICE: str = "Zephyr"
    DEFAULT_STUDENT_VOICE: str = "Puck"
    TARGET_AUDIO_DURATION: int = 300  # 5 minutes in seconds
    
    # Review Workflow Configuration
    DEFAULT_REVIEW_TIME_MINUTES: int = 15
    AUTO_APPROVAL_THRESHOLD: float = 0.85
    REVIEW_DUE_DAYS: int = 2
    MAX_REVIEW_ASSIGNMENTS: int = 10  # per educator
    
    # File Storage
    MAX_AUDIO_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    AUDIO_CLEANUP_DAYS: int = 30  # Delete old audio files after 30 days
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600  # 1 hour
    
    # Monitoring and Logging
    ENABLE_METRICS: bool = True
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @property
    def cosmos_connection_string(self) -> str:
        """Generate Cosmos DB connection string"""
        return f"AccountEndpoint={self.COSMOS_DB_ENDPOINT};AccountKey={self.COSMOS_DB_KEY};"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.is_production:
            # In production, only allow specific domains
            return [
                "https://your-production-domain.com",
                "https://your-staging-domain.com"
            ]
        else:
            # Development allows localhost variants
            return self.ALLOWED_ORIGINS


# Create global settings instance
settings = Settings()


# Validation
def validate_settings():
    """Validate critical configuration settings"""
    errors = []
    
    if not settings.GOOGLE_API_KEY:
        errors.append("GOOGLE_API_KEY is required")
    
    if not settings.COSMOS_DB_ENDPOINT:
        errors.append("COSMOS_DB_ENDPOINT is required")
        
    if not settings.COSMOS_DB_KEY:
        errors.append("COSMOS_DB_KEY is required")
    
    if settings.AUTO_APPROVAL_THRESHOLD < 0 or settings.AUTO_APPROVAL_THRESHOLD > 1:
        errors.append("AUTO_APPROVAL_THRESHOLD must be between 0 and 1")
    
    if settings.MAX_CONCURRENT_GENERATIONS < 1:
        errors.append("MAX_CONCURRENT_GENERATIONS must be at least 1")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")


# Validate on import
try:
    validate_settings()
except ValueError as e:
    if not settings.is_development:
        raise e
    else:
        print(f"⚠️  Configuration warning (development mode): {e}")