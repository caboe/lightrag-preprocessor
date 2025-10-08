"""
OpenAI-compatible chat models for the LightRAG Preprocessing API.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class ImageUrl(BaseModel):
    """Image URL model for multimodal content."""
    url: str = Field(..., description="Image URL or base64 data URL")
    detail: Optional[str] = Field(default="auto", description="Image detail level")


class ChatContent(BaseModel):
    """Chat content model supporting text and images."""
    type: str = Field(..., description="Content type: 'text' or 'image_url'")
    text: Optional[str] = Field(None, description="Text content")
    image_url: Optional[ImageUrl] = Field(None, description="Image URL content")
    
    @validator("type")
    def validate_content_type(cls, v):
        """Validate content type."""
        if v not in ["text", "image_url"]:
            raise ValueError("Content type must be 'text' or 'image_url'")
        return v
    
    @validator("text")
    def validate_text_content(cls, v, values):
        """Validate text content when type is text."""
        if values.get("type") == "text" and not v:
            raise ValueError("Text content is required when type is 'text'")
        return v
    
    @validator("image_url")
    def validate_image_content(cls, v, values):
        """Validate image content when type is image_url."""
        if values.get("type") == "image_url" and not v:
            raise ValueError("Image URL is required when type is 'image_url'")
        return v


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: 'system', 'user', or 'assistant'")
    content: Union[str, List[ChatContent]] = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional name for the message")
    
    @validator("role")
    def validate_role(cls, v):
        """Validate message role."""
        if v not in ["system", "user", "assistant"]:
            raise ValueError("Role must be 'system', 'user', or 'assistant'")
        return v


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str = Field(default="lightrag-proxy", description="Model identifier")
    messages: List[ChatMessage] = Field(..., min_items=1, description="List of chat messages")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4000, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")
    stream: Optional[bool] = Field(default=False, description="Whether to stream responses")
    user: Optional[str] = Field(None, description="User identifier")


class ChatCompletionChoice(BaseModel):
    """Chat completion choice model."""
    index: int = Field(..., description="Choice index")
    message: ChatMessage = Field(..., description="Generated message")
    finish_reason: str = Field(..., description="Reason for completion finish")


class ChatCompletionUsage(BaseModel):
    """Chat completion usage statistics."""
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total number of tokens")


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str = Field(..., description="Unique completion ID")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used for completion")
    choices: List[ChatCompletionChoice] = Field(..., description="List of completion choices")
    usage: Optional[ChatCompletionUsage] = Field(None, description="Token usage statistics")
    
    @validator("created", pre=True, always=True)
    def set_created_timestamp(cls, v):
        """Set creation timestamp if not provided."""
        if v is None:
            return int(datetime.utcnow().timestamp())
        return v


class ChatCompletionStreamChunk(BaseModel):
    """Chat completion stream chunk for streaming responses."""
    id: str = Field(..., description="Unique completion ID")
    object: str = Field(default="chat.completion.chunk", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used for completion")
    choices: List[Dict[str, Any]] = Field(..., description="Stream choices")
    
    @validator("created", pre=True, always=True)
    def set_created_timestamp(cls, v):
        """Set creation timestamp if not provided."""
        if v is None:
            return int(datetime.utcnow().timestamp())
        return v