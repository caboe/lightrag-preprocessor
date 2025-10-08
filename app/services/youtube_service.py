"""
YouTube service for transcript extraction and processing.
"""
import asyncio
import re
import uuid
from typing import Optional, Dict, Any
import structlog
from config.settings import settings

logger = structlog.get_logger(__name__)


class YouTubeService:
    """Service for extracting and processing YouTube video transcripts."""
    
    def __init__(self):
        """Initialize YouTube service."""
        self.timeout = settings.youtube_timeout
        self.languages = settings.youtube_languages_list
    
    def _extract_video_id(self, url: str) -> str:
        """
        Extract YouTube video ID from URL.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video ID string
            
        Raises:
            ValueError: If URL is invalid or video ID cannot be extracted
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    async def extract_transcript(self, url: str, language: str = "de") -> Dict[str, Any]:
        """
        Extract transcript from YouTube video.
        
        Args:
            url: YouTube video URL
            language: Preferred language for transcript (default: "de")
            
        Returns:
            Dictionary containing transcript data and metadata
            
        Raises:
            Exception: If transcript extraction fails
        """
        try:
            video_id = self._extract_video_id(url)
            logger.info("Extracting transcript", video_id=video_id, language=language)
            
            # Import youtube-transcript-api
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                from youtube_transcript_api._errors import (
                    TranscriptsDisabled, 
                    NoTranscriptFound, 
                    VideoUnavailable
                )
            except ImportError:
                raise Exception("youtube-transcript-api package is required. Install with: pip install youtube-transcript-api")
            
            # Try to get transcript in preferred language first
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = None
            used_language = language
            
            try:
                # Try preferred language
                transcript = transcript_list.find_transcript([language])
                logger.info("Found transcript in preferred language", language=language)
            except NoTranscriptFound:
                # Try fallback languages
                fallback_languages = [lang for lang in self.languages if lang != language]
                for fallback_lang in fallback_languages:
                    try:
                        transcript = transcript_list.find_transcript([fallback_lang])
                        used_language = fallback_lang
                        logger.info("Found transcript in fallback language", language=fallback_lang)
                        break
                    except NoTranscriptFound:
                        continue
                
                # If no manual transcript found, try auto-generated
                if transcript is None:
                    try:
                        transcript = transcript_list.find_generated_transcript([language])
                        used_language = language
                        logger.info("Found auto-generated transcript", language=language)
                    except NoTranscriptFound:
                        # Try auto-generated in fallback languages
                        for fallback_lang in fallback_languages:
                            try:
                                transcript = transcript_list.find_generated_transcript([fallback_lang])
                                used_language = fallback_lang
                                logger.info("Found auto-generated transcript in fallback", language=fallback_lang)
                                break
                            except NoTranscriptFound:
                                continue
            
            if transcript is None:
                raise Exception(f"No transcript found for video {video_id} in any supported language")
            
            # Fetch transcript data
            transcript_data = transcript.fetch()
            
            # Combine transcript text
            full_text = " ".join([entry['text'] for entry in transcript_data])
            
            # Get video metadata using yt-dlp
            video_metadata = await self._get_video_metadata(video_id)
            
            result = {
                "video_id": video_id,
                "video_title": video_metadata.get("title", f"YouTube Video {video_id}"),
                "transcript": full_text,
                "language": used_language,
                "duration": video_metadata.get("duration"),
                "transcript_entries": len(transcript_data),
                "is_auto_generated": transcript.is_generated,
                "url": url
            }
            
            logger.info(
                "Successfully extracted transcript",
                video_id=video_id,
                language=used_language,
                transcript_length=len(full_text),
                entries=len(transcript_data)
            )
            
            return result
            
        except TranscriptsDisabled:
            raise Exception(f"Transcripts are disabled for video: {url}")
        except VideoUnavailable:
            raise Exception(f"Video is unavailable: {url}")
        except Exception as e:
            logger.error("Failed to extract transcript", url=url, error=str(e))
            raise Exception(f"Failed to extract transcript: {str(e)}")
    
    async def _get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """
        Get video metadata using yt-dlp.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary containing video metadata
        """
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    f"https://www.youtube.com/watch?v={video_id}",
                    download=False
                )
                
                return {
                    "title": info.get("title", ""),
                    "duration": info.get("duration"),
                    "description": info.get("description", ""),
                    "uploader": info.get("uploader", ""),
                    "upload_date": info.get("upload_date", ""),
                    "view_count": info.get("view_count"),
                    "like_count": info.get("like_count"),
                }
                
        except ImportError:
            logger.warning("yt-dlp not available, using basic metadata")
            return {"title": f"YouTube Video {video_id}"}
        except Exception as e:
            logger.warning("Failed to get video metadata", video_id=video_id, error=str(e))
            return {"title": f"YouTube Video {video_id}"}
    
    async def process_youtube_video(self, url: str, language: str = "de") -> Dict[str, Any]:
        """
        Process YouTube video by extracting transcript and preparing for indexing.
        
        Args:
            url: YouTube video URL
            language: Preferred language for transcript
            
        Returns:
            Dictionary containing processed video data
        """
        try:
            # Extract transcript
            transcript_data = await self.extract_transcript(url, language)
            
            # Prepare content for indexing
            content = f"""Title: {transcript_data['video_title']}
URL: {transcript_data['url']}
Language: {transcript_data['language']}
Duration: {transcript_data.get('duration', 'Unknown')} seconds

Transcript:
{transcript_data['transcript']}"""
            
            return {
                "content": content,
                "metadata": {
                    "video_id": transcript_data["video_id"],
                    "video_title": transcript_data["video_title"],
                    "language": transcript_data["language"],
                    "duration": transcript_data.get("duration"),
                    "url": url,
                    "transcript_length": len(transcript_data["transcript"]),
                    "is_auto_generated": transcript_data.get("is_auto_generated", False)
                }
            }
            
        except Exception as e:
            logger.error("Failed to process YouTube video", url=url, error=str(e))
            raise


# Global service instance
youtube_service = YouTubeService()