"""
Configuration settings for LightRAG Preprocessing API.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Configuration
    app_name: str = "LightRAG Preprocessing API"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # LightRAG Configuration
    lightrag_base_url: str = Field(..., env="LIGHTRAG_BASE_URL")
    lightrag_api_key: str = Field(..., env="LIGHTRAG_API_KEY")
    lightrag_timeout: int = Field(default=30, env="LIGHTRAG_TIMEOUT")
    
    # Vision Model Configuration (OpenRouter)
    vision_model_base_url: str = Field(default="https://openrouter.ai/api/v1", env="VISION_MODEL_BASE_URL")
    vision_model_api_key: str = Field(..., env="VISION_MODEL_API_KEY")
    vision_model_name: str = Field(default="openai/gpt-4-vision-preview", env="VISION_MODEL_NAME")
    vision_model_timeout: int = Field(default=60, env="VISION_MODEL_TIMEOUT")
    vision_model_max_tokens: int = Field(default=1000, env="VISION_MODEL_MAX_TOKENS")
    
    # Application Security
    api_key: str = Field(..., env="API_KEY")
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # File Upload Configuration
    max_file_size: int = Field(default=50 * 1024 * 1024)  # 50MB
    max_image_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    allowed_file_types: str = Field(default=".pdf,.txt,.md,.docx")
    allowed_image_types: str = Field(default=".jpg,.jpeg,.png,.webp")
    
    # YouTube Configuration
    youtube_languages: str = Field(default="de,en")
    youtube_timeout: int = Field(default=30)
    
    # CORS Configuration
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8080")
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: str = Field(default="GET,POST,PUT,DELETE,OPTIONS")
    cors_allow_headers: str = Field(default="*")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Health Check Configuration
    health_check_timeout: int = Field(default=5, env="HEALTH_CHECK_TIMEOUT")
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v.lower()
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Get allowed file types as a list."""
        return [item.strip() for item in self.allowed_file_types.split(",") if item.strip()]
    
    @property
    def allowed_image_types_list(self) -> List[str]:
        """Get allowed image types as a list."""
        return [item.strip() for item in self.allowed_image_types.split(",") if item.strip()]
    
    @property
    def youtube_languages_list(self) -> List[str]:
        """Get YouTube languages as a list."""
        return [item.strip() for item in self.youtube_languages.split(",") if item.strip()]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]
    
    @property
    def cors_allow_methods_list(self) -> List[str]:
        """Get CORS allowed methods as a list."""
        return [item.strip() for item in self.cors_allow_methods.split(",") if item.strip()]
    
    @property
    def cors_allow_headers_list(self) -> List[str]:
        """Get CORS allowed headers as a list."""
        return [item.strip() for item in self.cors_allow_headers.split(",") if item.strip()]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings