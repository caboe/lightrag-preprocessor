"""
OpenAI service for multimodal LLM interactions.
"""
import asyncio
import base64
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Union
import structlog
from config.settings import settings
from app.models.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionUsage,
    ChatCompletionStreamChunk,
    ChatMessage,
    ChatContent,
)

logger = structlog.get_logger(__name__)


class OpenAIService:
    """Service for OpenAI API interactions."""
    
    def __init__(self):
        """Initialize Vision Model service (OpenRouter)."""
        self.api_key = settings.vision_model_api_key
        self.model = settings.vision_model_name
        self.base_url = settings.vision_model_base_url
        self._client = None
    
    async def _get_client(self):
        """Get or create HTTP client for OpenAI API."""
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=60.0
            )
        return self._client
    
    async def describe_image(self, image_data: bytes, image_format: str) -> str:
        """
        Generate a text description of an image using multimodal LLM.
        
        Args:
            image_data: Binary image data
            image_format: Image format (e.g., 'jpeg', 'png')
            
        Returns:
            Text description of the image
            
        Raises:
            Exception: If image description fails
        """
        try:
            logger.info("Generating image description", 
                       image_size=len(image_data),
                       image_format=image_format)
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            image_url = f"data:image/{image_format};base64,{image_base64}"
            
            # Prepare the chat completion request
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please provide a detailed description of this image. Focus on the main subjects, objects, actions, setting, and any notable details that would be useful for indexing and search purposes."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            client = await self._get_client()
            response = await client.post("/chat/completions", json=payload)
            
            if response.status_code != 200:
                error_msg = f"OpenAI image description failed: {response.status_code} - {response.text}"
                logger.error("OpenAI image description failed", 
                           status_code=response.status_code, 
                           error=response.text)
                raise Exception(error_msg)
            
            result = response.json()
            description = result["choices"][0]["message"]["content"]
            
            logger.info("Image description generated successfully", 
                       description_length=len(description))
            
            return description
            
        except Exception as e:
            logger.error("Failed to generate image description", error=str(e))
            raise
    
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Create a chat completion using OpenAI API.
        
        Args:
            request: Chat completion request
            
        Returns:
            Chat completion response
            
        Raises:
            Exception: If chat completion fails
        """
        try:
            logger.info("Creating chat completion", 
                       model=request.model,
                       messages_count=len(request.messages),
                       max_tokens=request.max_tokens)
            
            # Convert Pydantic models to dict for API call
            payload = {
                "model": self.model,  # Use configured model
                "messages": [self._convert_message_to_dict(msg) for msg in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
                "stream": request.stream
            }
            
            if request.stop:
                payload["stop"] = request.stop
            
            client = await self._get_client()
            response = await client.post("/chat/completions", json=payload)
            
            if response.status_code != 200:
                error_msg = f"OpenAI chat completion failed: {response.status_code} - {response.text}"
                logger.error("OpenAI chat completion failed", 
                           status_code=response.status_code, 
                           error=response.text)
                raise Exception(error_msg)
            
            result = response.json()
            
            # Convert response to our model
            completion_response = ChatCompletionResponse(
                id=result["id"],
                created=result["created"],
                model=result["model"],
                choices=[
                    ChatCompletionChoice(
                        index=choice["index"],
                        message=ChatMessage(
                            role=choice["message"]["role"],
                            content=choice["message"]["content"]
                        ),
                        finish_reason=choice["finish_reason"]
                    )
                    for choice in result["choices"]
                ],
                usage=ChatCompletionUsage(
                    prompt_tokens=result["usage"]["prompt_tokens"],
                    completion_tokens=result["usage"]["completion_tokens"],
                    total_tokens=result["usage"]["total_tokens"]
                ) if "usage" in result else None
            )
            
            logger.info("Chat completion created successfully", 
                       completion_id=completion_response.id,
                       total_tokens=completion_response.usage.total_tokens if completion_response.usage else None)
            
            return completion_response
            
        except Exception as e:
            logger.error("Failed to create chat completion", error=str(e))
            raise
    
    async def chat_completion_stream(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        """
        Create a streaming chat completion using OpenAI API.
        
        Args:
            request: Chat completion request
            
        Yields:
            Server-sent events for streaming response
            
        Raises:
            Exception: If streaming chat completion fails
        """
        try:
            logger.info("Creating streaming chat completion", 
                       model=request.model,
                       messages_count=len(request.messages))
            
            # Convert Pydantic models to dict for API call
            payload = {
                "model": self.model,  # Use configured model
                "messages": [self._convert_message_to_dict(msg) for msg in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
                "stream": True
            }
            
            if request.stop:
                payload["stop"] = request.stop
            
            client = await self._get_client()
            
            async with client.stream("POST", "/chat/completions", json=payload) as response:
                if response.status_code != 200:
                    # Try to get error details if available
                    error_details = ""
                    try:
                        error_details = await response.aread()
                        error_details = error_details.decode('utf-8')
                    except Exception:
                        pass
                    
                    error_msg = f"OpenAI streaming chat completion failed: {response.status_code}"
                    if error_details:
                        error_msg += f" - {error_details}"
                    
                    logger.error("OpenAI streaming chat completion failed",
                               status_code=response.status_code,
                               error_details=error_details)
                    raise Exception(error_msg)
                
                # Ensure response is properly initialized before streaming
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data.strip() == "[DONE]":
                            break
                        try:
                            yield f"data: {data}\n\n"
                        except Exception as stream_error:
                            logger.error("Error during streaming", error=str(stream_error))
                            break
            
            logger.info("Streaming chat completion completed successfully")
            
        except Exception as e:
            logger.error("Failed to create streaming chat completion", error=str(e))
            raise
    
    def _convert_message_to_dict(self, message: ChatMessage) -> Dict:
        """Convert ChatMessage to dictionary for API call."""
        result = {"role": message.role}
        
        if isinstance(message.content, str):
            result["content"] = message.content
        elif isinstance(message.content, list):
            result["content"] = []
            for content in message.content:
                if content.type == "text":
                    result["content"].append({
                        "type": "text",
                        "text": content.text
                    })
                elif content.type == "image_url":
                    result["content"].append({
                        "type": "image_url",
                        "image_url": {
                            "url": content.image_url.url,
                            "detail": content.image_url.detail
                        }
                    })
        
        if message.name:
            result["name"] = message.name
        
        return result
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global service instance
openai_service = OpenAIService()