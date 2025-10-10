"""
LightRAG service for document indexing and retrieval.
"""
import asyncio
import uuid
from typing import Optional
import structlog
from config.settings import settings

logger = structlog.get_logger(__name__)


class LightRAGService:
    """Service for interacting with LightRAG system."""
    
    def __init__(self):
        """Initialize LightRAG service."""
        self.api_key = settings.lightrag_api_key
        self.base_url = settings.lightrag_base_url
        self._client = None
    
    async def _get_client(self):
        """Get or create HTTP client for LightRAG API."""
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=settings.lightrag_timeout
            )
        return self._client
    
    async def index_text(self, text: str, title: Optional[str] = None) -> str:
        """
        Index text content in LightRAG.
        
        Args:
            text: Text content to index
            title: Optional title for the document
            
        Returns:
            Track ID for the indexing task
            
        Raises:
            Exception: If indexing fails
        """
        try:
            logger.info("Indexing text content", text_length=len(text), title=title)
            
            # Prepare the payload for LightRAG
            payload = {
                "text": text,
                "file_source": (title or "text").strip()
            }
            
            client = await self._get_client()
            response = await client.post("/documents/text", json=payload)
            
            if response.status_code != 200:
                error_msg = f"LightRAG indexing failed: {response.status_code} - {response.text}"
                logger.error("LightRAG indexing failed", 
                           status_code=response.status_code, 
                           error=response.text)
                raise Exception(error_msg)
            
            data = response.json()
            track_id = data.get("track_id")
            logger.info("Text content accepted for indexing", track_id=track_id)
            return track_id
            
        except Exception as e:
            logger.error("Failed to index text content", 
                        error=str(e))
            raise
    
    async def index_document(self, content: str, filename: str, file_type: str) -> str:
        """
        Index document content in LightRAG.
        
        Args:
            content: Extracted document content
            filename: Original filename
            file_type: File type/extension
            
        Returns:
            Track ID for the indexing task
            
        Raises:
            Exception: If indexing fails
        """
        try:
            logger.info("Indexing document content", 
                       filename=filename,
                       file_type=file_type,
                       content_length=len(content))
            
            # Prepare the payload for LightRAG
            payload = {
                "text": content,
                "file_source": filename
            }
            
            client = await self._get_client()
            response = await client.post("/documents/text", json=payload)
            
            if response.status_code != 200:
                error_msg = f"LightRAG document indexing failed: {response.status_code} - {response.text}"
                logger.error("LightRAG document indexing failed", 
                           status_code=response.status_code, 
                           error=response.text)
                raise Exception(error_msg)
            
            data = response.json()
            track_id = data.get("track_id")
            logger.info("Document content accepted for indexing", track_id=track_id)
            return track_id
            
        except Exception as e:
            logger.error("Failed to index document content", 
                        filename=filename,
                        error=str(e))
            raise
    
    async def query(self, query: str, max_results: int = 10) -> dict:
        """
        Query the LightRAG system.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Query results from LightRAG
            
        Raises:
            Exception: If query fails
        """
        try:
            logger.info("Querying LightRAG", query=query, max_results=max_results)
            
            payload = {
                "query": query,
                "max_results": max_results
            }
            
            client = await self._get_client()
            response = await client.post("/query", json=payload)
            
            if response.status_code != 200:
                error_msg = f"LightRAG query failed: {response.status_code} - {response.text}"
                logger.error("LightRAG query failed", 
                           status_code=response.status_code, 
                           error=response.text,
                           query=query)
                raise Exception(error_msg)
            
            result = response.json()
            logger.info("LightRAG query completed successfully", 
                       query=query, 
                       results_count=len(result.get("results", [])))
            
            return result
            
        except Exception as e:
            logger.error("Failed to query LightRAG", query=query, error=str(e))
            raise
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global service instance
lightrag_service = LightRAGService()