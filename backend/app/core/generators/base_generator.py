# backend/app/core/generators/base_generator.py
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)


class BaseContentGenerator(ABC):
    """Base class for all content generators with shared functionality"""
    
    def __init__(self, cosmos_service=None, blob_service=None):
        self.client = None
        self.types = types
        self.cosmos_service = cosmos_service
        self.blob_service = blob_service
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini client with configuration"""
        if not settings.GEMINI_API_KEY:
            raise ValueError(f"GEMINI_API_KEY is required. Please check your configuration in {settings.ENVIRONMENT} mode.")
        
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Gemini client initialized for {self.__class__.__name__} (Environment: {settings.ENVIRONMENT})")
    
    def _extract_grade_info(self, request) -> str:
        """Extract grade information from request with fallback"""
        return getattr(request, 'grade', None) or "appropriate grade level"
    
    def _serialize_datetime_fields(self, data):
        """
        Recursively convert all datetime objects to ISO format strings
        """
        if isinstance(data, dict):
            return {key: self._serialize_datetime_fields(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._serialize_datetime_fields(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
    
    def _format_terminology_string(self, key_terminology: Dict[str, str]) -> str:
        """Format terminology dictionary into a readable string"""
        return "\n".join([f"- {term}: {defn}" for term, defn in key_terminology.items()])
    
    def _safe_json_loads(self, response_text: str, operation_name: str):
        """Safely parse JSON response with error handling"""
        try:
            import json
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"{operation_name} JSON parsing failed: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise ValueError(f"{operation_name} returned invalid JSON") from e
    
    def _handle_generation_error(self, operation_name: str, error: Exception):
        """Standard error handling for generation operations"""
        error_msg = f"{operation_name} failed: {str(error)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from error