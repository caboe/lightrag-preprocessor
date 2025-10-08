"""
Models package for the LightRAG Preprocessing API.
"""
from .base import (
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    ErrorDetail,
    HealthStatus,
    ServiceHealth,
)
from .documents import (
    TextInputRequest,
    DocumentUploadResponse,
    TextInputResponse,
    ImageProcessingResponse,
    YouTubeRequest,
    YouTubeResponse,
)
from .chat import (
    ImageUrl,
    ChatContent,
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionChoice,
    ChatCompletionUsage,
    ChatCompletionResponse,
    ChatCompletionStreamChunk,
)

__all__ = [
    # Base models
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "ErrorDetail",
    "HealthStatus",
    "ServiceHealth",
    # Document models
    "TextInputRequest",
    "DocumentUploadResponse",
    "TextInputResponse",
    "ImageProcessingResponse",
    "YouTubeRequest",
    "YouTubeResponse",
    # Chat models
    "ImageUrl",
    "ChatContent",
    "ChatMessage",
    "ChatCompletionRequest",
    "ChatCompletionChoice",
    "ChatCompletionUsage",
    "ChatCompletionResponse",
    "ChatCompletionStreamChunk",
]