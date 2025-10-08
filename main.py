"""
LightRAG Preprocessing API - Main FastAPI Application
"""
import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config.settings import settings
from app.models.base import SuccessResponse, ErrorResponse
from app.models.chat import ChatCompletionRequest, ChatCompletionResponse
from app.models.documents import (
    TextInputRequest, 
    DocumentUploadResponse, 
    TextInputResponse,
    ImageProcessingResponse,
    YouTubeRequest,
    YouTubeResponse
)
from app.services.openai_service import openai_service
from app.services.lightrag_service import lightrag_service
from app.services.youtube_service import youtube_service

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting LightRAG Preprocessing API", version=settings.app_version)
    yield
    logger.info("Shutting down LightRAG Preprocessing API")
    
    # Cleanup services
    await openai_service.close()
    await lightrag_service.close()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for preprocessing documents, images, and YouTube videos for LightRAG knowledge graphs",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers_list,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)


# Authentication dependency
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key authentication."""
    if credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# Utility functions
def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate file type based on extension."""
    return any(filename.lower().endswith(ext) for ext in allowed_types)


def validate_file_size(file_size: int, max_size: int) -> bool:
    """Validate file size."""
    return file_size <= max_size


# Health check endpoints
@app.get("/health", response_model=SuccessResponse)
async def health_check():
    """Basic health check endpoint."""
    return SuccessResponse(message="Service is healthy")


@app.get("/health/detailed")
async def detailed_health_check(api_key: str = Depends(verify_api_key)):
    """Detailed health check with external service status."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }
    
    # Check OpenAI service
    try:
        # Simple test to verify OpenAI connection
        test_response = await openai_service._get_client()
        health_status["services"]["openai"] = "healthy"
    except Exception as e:
        health_status["services"]["openai"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check LightRAG service
    try:
        # Simple test to verify LightRAG connection
        test_response = await lightrag_service._get_client()
        health_status["services"]["lightrag"] = "healthy"
    except Exception as e:
        health_status["services"]["lightrag"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


# Document processing endpoints
@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Upload and process a document file."""
    start_time = time.time()
    
    try:
        # Validate file type
        if not validate_file_type(file.filename, settings.allowed_file_types_list):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Supported types: {settings.allowed_file_types_list}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        if not validate_file_size(file_size, settings.MAX_FILE_SIZE):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Extract text content based on file type
        text_content = content.decode('utf-8')  # Simple text extraction
        
        # Index document in LightRAG
        document_id = await lightrag_service.index_document(
            content=text_content,
            filename=file.filename,
            file_type=file.content_type or "text/plain"
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            "Document uploaded successfully",
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            processing_time=processing_time
        )
        
        return DocumentUploadResponse(
            message="Document uploaded and indexed successfully",
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            file_type=file.content_type,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload document", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@app.post("/documents/text", response_model=TextInputResponse)
async def process_text(
    request: TextInputRequest,
    api_key: str = Depends(verify_api_key)
):
    """Process and index text content."""
    start_time = time.time()
    
    try:
        # Index text in LightRAG
        document_id = await lightrag_service.index_text(
            text=request.text,
            title=request.title
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            "Text processed successfully",
            document_id=document_id,
            text_length=len(request.text),
            title=request.title,
            processing_time=processing_time
        )
        
        return TextInputResponse(
            message="Text processed and indexed successfully",
            document_id=document_id,
            text_length=len(request.text),
            title=request.title,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error("Failed to process text", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process text: {str(e)}"
        )


@app.post("/images/process", response_model=ImageProcessingResponse)
async def process_image(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Process an image and generate text description."""
    start_time = time.time()
    
    try:
        # Validate file type
        if not validate_file_type(file.filename, settings.allowed_image_types_list):
            raise HTTPException(
                status_code=400,
                detail=f"Image type not allowed. Supported types: {settings.allowed_image_types_list}"
            )
        
        # Read image content
        image_data = await file.read()
        image_size = len(image_data)
        
        # Validate image size
        if not validate_file_size(image_size, settings.MAX_IMAGE_SIZE):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image too large. Maximum size: {settings.MAX_IMAGE_SIZE} bytes"
            )
        
        # Get image format
        image_format = file.content_type or "image/jpeg"
        
        # Generate description using OpenAI
        description = await openai_service.describe_image(image_data, image_format)
        
        # Index description in LightRAG
        document_id = await lightrag_service.index_text(
            text=f"Image Description: {description}",
            title=f"Image: {file.filename}"
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            "Image processed successfully",
            document_id=document_id,
            filename=file.filename,
            image_size=image_size,
            description_length=len(description),
            processing_time=processing_time
        )
        
        return ImageProcessingResponse(
            message="Image processed and description indexed successfully",
            document_id=document_id,
            description=description,
            image_size=image_size,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process image", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )


@app.post("/youtube/process", response_model=YouTubeResponse)
async def process_youtube(
    request: YouTubeRequest,
    api_key: str = Depends(verify_api_key)
):
    """Process YouTube video by extracting and indexing transcript."""
    start_time = time.time()
    
    try:
        # Process YouTube video
        video_data = await youtube_service.process_youtube_video(
            url=request.url,
            language=request.language
        )
        
        # Index transcript in LightRAG
        document_id = await lightrag_service.index_text(
            text=video_data["content"],
            title=f"YouTube: {video_data['metadata']['video_title']}"
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            "YouTube video processed successfully",
            document_id=document_id,
            video_id=video_data["metadata"]["video_id"],
            video_title=video_data["metadata"]["video_title"],
            transcript_length=video_data["metadata"]["transcript_length"],
            processing_time=processing_time
        )
        
        return YouTubeResponse(
            message="YouTube video processed and transcript indexed successfully",
            document_id=document_id,
            video_title=video_data["metadata"]["video_title"],
            video_id=video_data["metadata"]["video_id"],
            transcript_length=video_data["metadata"]["transcript_length"],
            language=video_data["metadata"]["language"],
            duration=video_data["metadata"].get("duration"),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error("Failed to process YouTube video", url=request.url, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process YouTube video: {str(e)}"
        )


# OpenAI-compatible chat endpoint
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    api_key: str = Depends(verify_api_key)
):
    """OpenAI-compatible chat completions endpoint."""
    try:
        if request.stream:
            # Return streaming response
            async def generate():
                async for chunk in openai_service.chat_completion_stream(request):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # Return regular response
            response = await openai_service.chat_completion(request)
            return response
            
    except Exception as e:
        logger.error("Failed to process chat completion", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat completion: {str(e)}"
        )


# Query endpoint for LightRAG
@app.post("/query")
async def query_knowledge_graph(
    query: str = Form(...),
    max_results: int = Form(default=10),
    api_key: str = Depends(verify_api_key)
):
    """Query the LightRAG knowledge graph."""
    try:
        results = await lightrag_service.query(query, max_results)
        return results
        
    except Exception as e:
        logger.error("Failed to query knowledge graph", query=query, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query knowledge graph: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
    