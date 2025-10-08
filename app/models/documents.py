"""
Document processing models for the LightRAG Preprocessing API.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from .base import SuccessResponse


class TextInputRequest(BaseModel):
    """Text input request model."""
    text: str = Field(..., min_length=1, max_length=100000, description="Text content to index")
    title: Optional[str] = Field(None, max_length=200, description="Optional title for the text document")
    
    @validator("text")
    def validate_text(cls, v):
        """Validate text content."""
        if not v.strip():
            raise ValueError("Text content cannot be empty")
        return v.strip()


class DocumentUploadResponse(SuccessResponse):
    """Document upload response model."""
    document_id: str = Field(..., description="Unique identifier for the indexed document")
    filename: Optional[str] = Field(None, description="Original filename")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_type: Optional[str] = Field(None, description="File type/extension")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class TextInputResponse(SuccessResponse):
    """Text input response model."""
    document_id: str = Field(..., description="Unique identifier for the indexed text")
    text_length: int = Field(..., description="Length of the processed text")
    title: Optional[str] = Field(None, description="Document title")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class ImageProcessingResponse(SuccessResponse):
    """Image processing response model."""
    document_id: str = Field(..., description="Unique identifier for the indexed description")
    description: str = Field(..., description="Generated text description of the image")
    image_size: Optional[int] = Field(None, description="Image file size in bytes")
    image_dimensions: Optional[str] = Field(None, description="Image dimensions (width x height)")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class YouTubeRequest(BaseModel):
    """YouTube processing request model."""
    url: str = Field(..., description="YouTube video URL")
    language: Optional[str] = Field(default="de", description="Preferred language for transcript")
    
    @validator("url")
    def validate_youtube_url(cls, v):
        """Validate YouTube URL."""
        if not v.strip():
            raise ValueError("URL cannot be empty")
        
        # Basic YouTube URL validation
        youtube_domains = ["youtube.com", "youtu.be", "www.youtube.com", "m.youtube.com"]
        if not any(domain in v.lower() for domain in youtube_domains):
            raise ValueError("Invalid YouTube URL")
        
        return v.strip()
    
    @validator("language")
    def validate_language(cls, v):
        """Validate language code."""
        if v and len(v) != 2:
            raise ValueError("Language code must be 2 characters (e.g., 'de', 'en')")
        return v.lower() if v else "de"


class YouTubeResponse(SuccessResponse):
    """YouTube processing response model."""
    document_id: str = Field(..., description="Unique identifier for the indexed transcript")
    video_title: str = Field(..., description="Title of the YouTube video")
    video_id: str = Field(..., description="YouTube video ID")
    transcript_length: int = Field(..., description="Length of the extracted transcript")
    language: str = Field(..., description="Language of the extracted transcript")
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")