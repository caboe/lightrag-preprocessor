"""
LightRAG Preprocessing API - Main FastAPI Application
"""
import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional
import os
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse

from config.settings import settings
from app.models.base import SuccessResponse, ErrorResponse
from app.models.chat import (
    ChatCompletionRequest, 
    ChatCompletionResponse, 
    ChatCompletionChoice, 
    ChatCompletionUsage, 
    ChatMessage,
    ChatContent
)
from app.models.documents import (
    TextInputRequest, 
    DocumentUploadResponse, 
    TextInputResponse,
    ImageProcessingResponse,
    YouTubeRequest,
    YouTubeResponse,
    QueryRequest,
    QueryResponse
)
from app.services.openai_service import openai_service
from app.services.lightrag_service import lightrag_service
from app.services.youtube_service import youtube_service
from app.services.pdf_service import pdf_service

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
# Switch to X-API-Key header authentication (no Bearer tokens)

# Selective Bearer support for specific endpoints
bearer_security = HTTPBearer(auto_error=False)


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
    allowed_hosts=["*"]
)


# Authentication dependency
async def verify_api_key(x_api_key: str | None = Header(default=None, alias="x-api-key")):
    """Verify API key via X-API-Key header."""
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key

async def verify_upload_auth(
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
):
    """Verify auth for document upload: accept X-API-Key or Authorization: Bearer."""
    # Prefer X-API-Key if provided
    if x_api_key:
        if x_api_key == settings.api_key:
            return x_api_key
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Fallback to Bearer token
    if credentials and (credentials.scheme or "").lower() == "bearer":
        token = credentials.credentials
        # Token must match one of the configured chat API keys
        if token in settings.chat_api_keys_list:
            return token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing credentials",
    )

async def verify_chat_auth(
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
):
    """Verify auth for chat: accept X-API-Key or Authorization: Bearer.
    - X-API-Key must match `settings.api_key`
    - Bearer token must match one of `settings.chat_api_keys_list`
    """
    if x_api_key:
        if x_api_key == settings.api_key:
            return x_api_key
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if credentials and (credentials.scheme or "").lower() == "bearer":
        token = credentials.credentials
        if token in settings.chat_api_keys_list:
            return token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing credentials",
    )

# Utility functions
def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate file type based on extension."""
    return any(filename.lower().endswith(ext) for ext in allowed_types)


def validate_file_size(file_size: int, max_size: int) -> bool:
    """Validate file size."""
    return file_size <= max_size


async def _process_chat_messages(messages: List[ChatMessage]) -> List[ChatMessage]:
    """
    Process chat messages, converting images to text descriptions.
    
    Args:
        messages: List of chat messages
        
    Returns:
        List of processed messages with images converted to text
    """
    processed_messages = []
    
    for message in messages:
        if isinstance(message.content, str):
            # Simple text message
            processed_messages.append(message)
        elif isinstance(message.content, list):
            # Multi-modal message with potential images
            processed_content = []
            
            for content_item in message.content:
                if content_item.type == "text":
                    processed_content.append(content_item.text)
                elif content_item.type == "image_url" and content_item.image_url:
                    try:
                        # Download and describe the image
                        image_url = content_item.image_url.url
                        
                        if image_url.startswith("data:image"):
                            # Base64 encoded image
                            import base64
                            header, data = image_url.split(",", 1)
                            image_data = base64.b64decode(data)
                            image_format = header.split(";")[0].split("/")[1]
                        else:
                            # URL image - download it
                            import httpx
                            async with httpx.AsyncClient() as client:
                                response = await client.get(image_url)
                                response.raise_for_status()
                                image_data = response.content
                                content_type = response.headers.get("content-type", "")
                                image_format = content_type.split("/")[-1] if "/" in content_type else "jpeg"
                        
                        # Generate description using OpenAI service
                        description = await openai_service.describe_image(image_data, image_format)
                        processed_content.append(f"[Image description: {description}]")
                        
                        logger.info("Processed image in chat message", 
                                  image_format=image_format, 
                                  description_length=len(description))
                        
                    except Exception as e:
                        logger.error("Failed to process image in chat message", error=str(e))
                        processed_content.append("[Image: Unable to process image]")
            
            # Create new message with processed content
            processed_message = ChatMessage(
                role=message.role,
                content=" ".join(processed_content),
                name=message.name
            )
            processed_messages.append(processed_message)
        else:
            # Fallback for other content types
            processed_messages.append(message)
    
    return processed_messages


def _create_search_query(messages: List[ChatMessage]) -> str:
    """
    Create a search query from chat messages.
    
    Args:
        messages: List of processed chat messages
        
    Returns:
        Search query string for LightRAG
    """
    # Extract context from previous messages
    context_parts = []
    current_question = ""
    
    for message in messages:
        content = message.content if isinstance(message.content, str) else str(message.content)
        
        if message.role == "system":
            context_parts.append(f"System: {content}")
        elif message.role == "user":
            if len(messages) > 1 and message == messages[-1]:
                # Last user message is the current question
                current_question = content
            else:
                context_parts.append(f"User: {content}")
        elif message.role == "assistant":
            context_parts.append(f"Assistant: {content}")
    
    # Build search query
    if context_parts and current_question:
        context = " ".join(context_parts[-3:])  # Last 3 context messages
        search_query = f"Context: {context}. Current question: {current_question}"
    elif current_question:
        search_query = current_question
    else:
        # Fallback to last message content
        last_message = messages[-1] if messages else None
        if last_message:
            search_query = last_message.content if isinstance(last_message.content, str) else str(last_message.content)
        else:
            search_query = "General information request"
    
    logger.info("Created search query for LightRAG", 
               query_length=len(search_query),
               messages_count=len(messages))
    
    return search_query


def _format_lightrag_response(lightrag_response: dict) -> str:
    """
    Format LightRAG response for chat completion.
    
    Args:
        lightrag_response: Response from LightRAG query
        
    Returns:
        Formatted response content
    """
    try:
        results = lightrag_response.get("results", [])
        query = lightrag_response.get("query", "")
        
        if not results:
            return "I don't have specific information about that topic in my knowledge base. Could you please provide more details or ask about something else?"
        
        # Format the response based on search results
        response_parts = []
        
        # Add a brief introduction
        response_parts.append("Based on the information in my knowledge base:")
        response_parts.append("")
        
        # Add relevant results
        for i, result in enumerate(results[:3], 1):  # Limit to top 3 results
            content = result.get("content", "").strip()
            if content:
                response_parts.append(f"{i}. {content}")
        
        # Add source information if available
        if len(results) > 3:
            response_parts.append("")
            response_parts.append(f"(Found {len(results)} total relevant sources)")
        
        formatted_response = "\n".join(response_parts)
        
        logger.info("Formatted LightRAG response", 
                   results_count=len(results),
                   response_length=len(formatted_response))
        
        return formatted_response
        
    except Exception as e:
        logger.error("Failed to format LightRAG response", error=str(e))
        return "I encountered an error while processing the information. Please try asking your question again."


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
    api_key: str = Depends(verify_upload_auth)
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
        if not validate_file_size(file_size, settings.max_file_size):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Extract text content based on file type
        ext = os.path.splitext(file.filename)[1].lower()
        try:
            if ext == ".pdf" or (file.content_type and "pdf" in file.content_type.lower()):
                # Extract text from PDF using PyMuPDF
                import fitz  # PyMuPDF
                pdf = fitz.open(stream=content, filetype="pdf")
                pages_text = []
                for page in pdf:
                    pages_text.append(page.get_text())
                pdf.close()
                text_content = "\n".join(pages_text).strip()
            elif ext in (".txt", ".md") or (file.content_type and file.content_type.startswith("text/")):
                # Decode plain text with fallback
                try:
                    text_content = content.decode("utf-8")
                except UnicodeDecodeError:
                    text_content = content.decode("latin-1", errors="replace")
            elif ext == ".docx" or (file.content_type and "word" in (file.content_type.lower())):
                # DOCX not yet supported without additional dependency
                raise HTTPException(
                    status_code=400,
                    detail="DOCX extraction is not supported yet. Please upload PDF or TXT/MD."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type for text extraction: {ext or file.content_type}"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to extract text from document", filename=file.filename, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract text from document: {str(e)}"
            )
        
        # Index document in LightRAG
        track_id = await lightrag_service.index_document(
            content=text_content,
            filename=file.filename,
            file_type=file.content_type or "text/plain"
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            "Document uploaded successfully",
            track_id=track_id,
            filename=file.filename,
            file_size=file_size,
            processing_time=processing_time
        )
        
        return DocumentUploadResponse(
            message="Document uploaded and indexed successfully",
            track_id=track_id,
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
    """Process text content by generating a PDF and indexing it."""
    start_time = time.time()
    
    try:
        # Validate text content
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content cannot be empty"
            )
        
        # Generate PDF from text
        logger.info("Generating PDF from text input", 
                   text_length=len(request.text), 
                   title=request.title)
        
        pdf_bytes, pdf_filename = await pdf_service.generate_pdf_from_text(
            text=request.text,
            title=request.title,
            author="LightRAG Preprocessor"
        )
        
        # Validate generated PDF size
        pdf_size = len(pdf_bytes)
        if not validate_file_size(pdf_size, settings.max_file_size):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Generated PDF too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Extract text content from the generated PDF for indexing
        # (We could send the original text, but this ensures consistency with the PDF)
        import fitz  # PyMuPDF
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_text = []
        for page in pdf_doc:
            pages_text.append(page.get_text())
        pdf_doc.close()
        extracted_text = "\n".join(pages_text).strip()
        
        # Index the document in LightRAG using the PDF filename
        track_id = await lightrag_service.index_document(
            content=extracted_text,
            filename=pdf_filename,
            file_type="application/pdf"
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            "Text processed and PDF generated successfully",
            track_id=track_id,
            text_length=len(request.text),
            title=request.title,
            pdf_filename=pdf_filename,
            pdf_size=pdf_size,
            processing_time=processing_time
        )
        
        return TextInputResponse(
            message="Text processed, PDF generated, and indexed successfully",
            track_id=track_id,
            text_length=len(request.text),
            title=request.title,
            processing_time=processing_time,
            pdf_filename=pdf_filename,
            pdf_size=pdf_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process text and generate PDF", error=str(e))
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
        if not validate_file_size(image_size, settings.max_image_size):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image too large. Maximum size: {settings.max_image_size} bytes"
            )
        
        # Get image format
        image_format = file.content_type or "image/jpeg"
        
        # Generate description using OpenAI
        description = await openai_service.describe_image(image_data, image_format)
        
        # Index description in LightRAG
        track_id = await lightrag_service.index_text(
            text=f"Image Description: {description}",
            title=f"Image: {file.filename}"
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            "Image processed successfully",
            track_id=track_id,
            filename=file.filename,
            image_size=image_size,
            description_length=len(description),
            processing_time=processing_time
        )
        
        return ImageProcessingResponse(
            message="Image processed and description indexed successfully",
            track_id=track_id,
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
        track_id = await lightrag_service.index_text(
            text=video_data["content"],
            title=f"YouTube: {video_data['metadata']['video_title']}"
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            "YouTube video processed successfully",
            track_id=track_id,
            video_id=video_data["metadata"]["video_id"],
            video_title=video_data["metadata"]["video_title"],
            transcript_length=video_data["metadata"]["transcript_length"],
            processing_time=processing_time
        )
        
        return YouTubeResponse(
            message="YouTube video processed and transcript indexed successfully",
            track_id=track_id,
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
    api_key: str = Depends(verify_chat_auth)
):
    """OpenAI-compatible chat completions endpoint using LightRAG."""
    try:
        # Process messages and handle images
        processed_messages = await _process_chat_messages(request.messages)
        
        # Create search query from conversation context
        search_query = _create_search_query(processed_messages)
        
        # Query LightRAG knowledge graph
        lightrag_response = await lightrag_service.query(search_query, max_results=5)
        
        # Format response as OpenAI chat completion
        if request.stream:
            # Return streaming response
            async def generate():
                response_content = _format_lightrag_response(lightrag_response)
                
                # Create streaming chunks
                completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
                created_timestamp = int(time.time())
                
                # Send initial chunk
                chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_timestamp,
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"role": "assistant", "content": ""},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                
                # Send content in chunks
                words = response_content.split()
                for i, word in enumerate(words):
                    chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created_timestamp,
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": word + " "},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.01)  # Small delay for streaming effect
                
                # Send final chunk
                chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_timestamp,
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # Return regular response
            response_content = _format_lightrag_response(lightrag_response)
            
            response = ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                object="chat.completion",
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=response_content
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=ChatCompletionUsage(
                    prompt_tokens=len(search_query.split()),
                    completion_tokens=len(response_content.split()),
                    total_tokens=len(search_query.split()) + len(response_content.split())
                )
            )
            return response
            
    except Exception as e:
        logger.error("Failed to process chat completion", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat completion: {str(e)}"
        )


# Query endpoint for LightRAG
@app.post("/query", response_model=QueryResponse)
async def query_knowledge_graph(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """Query the LightRAG knowledge graph."""
    try:
        start_time = time.time()
        results = await lightrag_service.query(request.query, request.max_results)
        processing_time = time.time() - start_time
        
        # Ensure results is a list of dictionaries
        if not isinstance(results, list):
            results = []
        
        # Convert results to QueryResult objects
        query_results = []
        for result in results:
            if isinstance(result, dict):
                query_results.append({
                    "document_id": result.get("id", ""),
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                })
        
        return QueryResponse(
            query=request.query,
            results=query_results,
            total_results=len(query_results),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error("Failed to query knowledge graph", query=request.query, error=str(e))
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
    