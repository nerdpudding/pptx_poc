#!/usr/bin/env python3
"""
PPTX POC - Ollama Client
Async HTTP client for Ollama API with prompt templates, JSON parsing, and error handling
"""

import logging
import json
import re
from typing import Optional, Dict, Any
from enum import Enum

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

from config import Settings, get_settings

# Configure logging
logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

class SlideType(str, Enum):
    """Types of slides for prompt generation"""
    TITLE = "title"
    CONTENT = "content"
    SUMMARY = "summary"

# =============================================================================
# Models
# =============================================================================

class OllamaRequest(BaseModel):
    """Ollama API request model"""
    model: str
    prompt: str
    stream: bool = False
    format: Optional[str] = None  # "json" for JSON mode
    options: Optional[Dict[str, Any]] = None

class OllamaResponse(BaseModel):
    """Ollama API response model"""
    model: str
    created_at: str
    response: str
    done: bool
    context: Optional[list[int]] = None

class SlideContent(BaseModel):
    """Structured slide content from Ollama response"""
    type: SlideType
    heading: str = Field(..., min_length=1, max_length=200)
    subheading: Optional[str] = Field(default=None, max_length=300)
    bullets: Optional[list[str]] = Field(default=None, max_items=10)

class PresentationContent(BaseModel):
    """Complete presentation structure"""
    title: str = Field(..., min_length=1, max_length=200)
    slides: list[SlideContent] = Field(..., min_length=1, max_length=20)

# =============================================================================
# Ollama Client Class
# =============================================================================

class OllamaClient:
    """Async HTTP client for Ollama API with retry logic and JSON parsing"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.ollama_host.rstrip('/')
        self.timeout = httpx.Timeout(settings.ollama_timeout)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )

    async def __aenter__(self):
        """Async context manager entry"""
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    # =============================================================================
    # Core Methods
    # =============================================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def generate_presentation(
        self,
        topic: str,
        language: str = "en",
        slides: int = 3,
        temperature: Optional[float] = None,
        num_ctx: Optional[int] = None
    ) -> PresentationContent:
        """
        Generate presentation content using Ollama

        Args:
            topic: Presentation topic
            language: Language code (en, nl, de, fr)
            slides: Number of slides to generate
            temperature: Optional override for Ollama temperature (0.0-2.0)
            num_ctx: Optional override for context window size

        Returns:
            PresentationContent with structured slide data

        Raises:
            HTTPException: If generation fails after retries
        """
        # Use provided values or fall back to config defaults
        effective_temp = temperature if temperature is not None else self.settings.ollama_temperature
        effective_ctx = num_ctx if num_ctx is not None else self.settings.ollama_num_ctx

        logger.info(f"Generating presentation: topic='{topic}', language='{language}', slides={slides}, temp={effective_temp}, ctx={effective_ctx}")

        # Build prompt template
        prompt = self._build_presentation_prompt(topic, language, slides)

        try:
            # Send request to Ollama with options
            response = await self._send_ollama_request(
                prompt,
                temperature=effective_temp,
                num_ctx=effective_ctx
            )

            # Parse JSON response
            presentation_data = self._parse_ollama_response(response)

            # Validate and return structured content
            return self._validate_presentation_content(presentation_data)

        except RetryError as e:
            logger.error(f"Ollama request failed after retries: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error": {
                        "code": "OLLAMA_TIMEOUT",
                        "message": "Ollama service is unavailable. Please try again later."
                    }
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error generating presentation: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": {
                        "code": "GENERATION_ERROR",
                        "message": "Failed to generate presentation content."
                    }
                }
            )

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _build_presentation_prompt(
        self,
        topic: str,
        language: str,
        slides: int
    ) -> str:
        """
        Build structured prompt for presentation generation

        Returns:
            Formatted prompt string for Ollama
        """
        # Ensure slides is within reasonable bounds
        slides = max(1, min(slides, self.settings.max_slides))

        prompt = f"""
        Generate a professional PowerPoint presentation outline in {language} about: "{topic}"

        Requirements:
        1. Return ONLY valid JSON - no additional text
        2. Structure must match exactly:
        {{
            "title": "Presentation title",
            "slides": [
                {{
                    "type": "title|content|summary",
                    "heading": "Slide heading",
                    "subheading": "Optional subheading",
                    "bullets": ["Bullet point 1", "Bullet point 2"]
                }}
            ]
        }}

        Presentation should have exactly {slides} slides:
        - Slide 1: Title slide with main topic and subheading
        - Slides 2 to {slides - 1}: Content slides with key points
        - Slide {slides}: Summary slide

        Focus on professional, concise content suitable for business presentations.
        Use clear headings and bullet points.
        """

        logger.debug(f"Built prompt for topic '{topic}' with {slides} slides")
        return prompt.strip()

    async def _send_ollama_request(
        self,
        prompt: str,
        temperature: float,
        num_ctx: int
    ) -> str:
        """
        Send request to Ollama API with retry logic

        Args:
            prompt: The prompt to send to Ollama
            temperature: Sampling temperature (0.0-2.0)
            num_ctx: Context window size

        Returns:
            Raw response text from Ollama

        Raises:
            httpx.RequestError: If request fails
            httpx.HTTPStatusError: If HTTP error occurs
        """
        request_data = OllamaRequest(
            model=self.settings.ollama_model,
            prompt=prompt,
            stream=False,
            format="json",  # Force JSON output from Ollama
            options={
                "temperature": temperature,
                "num_ctx": num_ctx
            }
        )

        logger.debug(f"Sending request to Ollama: {self.base_url}/api/generate")

        response = await self.client.post(
            "/api/generate",
            json=request_data.dict()
        )

        # Ensure successful response
        response.raise_for_status()

        # Extract and return the response text
        response_data = response.json()
        return response_data.get("response", "")

    def _parse_ollama_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Ollama response text into structured data

        Args:
            response_text: Raw text from Ollama

        Returns:
            Parsed dictionary with presentation data

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            # Clean response text (remove any non-JSON content)
            clean_text = self._clean_json_response(response_text)

            # Parse JSON
            data = json.loads(clean_text)

            # Validate basic structure
            if not isinstance(data, dict):
                raise ValueError("Response is not a JSON object")

            if "title" not in data or "slides" not in data:
                raise ValueError("Missing required fields: title, slides")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response: {e}")

    def _clean_json_response(self, text: str) -> str:
        """
        Clean Ollama response to extract valid JSON

        Handles:
        - Markdown code blocks (```json ... ```)
        - Extra text before/after JSON
        - Whitespace issues

        Args:
            text: Raw response text

        Returns:
            Cleaned text containing only JSON
        """
        # Remove markdown code blocks
        text = re.sub(r'```json\s*\n?', '', text)
        text = re.sub(r'```\s*\n?', '', text)
        text = text.strip()

        # Find first { and last } to extract JSON object
        start = text.find('{')
        end = text.rfind('}')

        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]

        # Fallback: return as-is and let JSON parser handle errors
        return text

    def _validate_presentation_content(self, data: Dict[str, Any]) -> PresentationContent:
        """
        Validate and convert presentation data to Pydantic model

        Args:
            data: Parsed presentation data

        Returns:
            Validated PresentationContent model

        Raises:
            ValidationError: If data doesn't match expected structure
        """
        try:
            # Convert to PresentationContent model
            return PresentationContent(**data)

        except ValidationError as e:
            logger.error(f"Presentation content validation failed: {e}")
            raise ValueError(f"Invalid presentation structure: {e}")

    # =========================================================================
    # Streaming Generator
    # =========================================================================

    async def stream_generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        num_ctx: Optional[int] = None,
        num_predict: Optional[int] = None,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        min_p: Optional[float] = None,
        repeat_penalty: Optional[float] = None,
        repeat_last_n: Optional[int] = None,
        seed: Optional[int] = None,
        format_json: bool = False
    ):
        """
        Stream generate response from Ollama.
        Yields chunks as they arrive.

        Args:
            prompt: The prompt to send
            system: Optional system message
            temperature: Sampling temperature
            num_ctx: Context window size
            num_predict: Max tokens to generate
            top_k: Top-K sampling
            top_p: Top-P / nucleus sampling
            min_p: Min-P sampling
            repeat_penalty: Repetition penalty
            repeat_last_n: Tokens to look back for repetition
            seed: Random seed
            format_json: Force JSON output

        Yields:
            Dict with 'response' text and 'done' status
        """
        # Build options dict with only provided values
        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if num_ctx is not None:
            options["num_ctx"] = num_ctx
        if num_predict is not None:
            options["num_predict"] = num_predict
        if top_k is not None:
            options["top_k"] = top_k
        if top_p is not None:
            options["top_p"] = top_p
        if min_p is not None:
            options["min_p"] = min_p
        if repeat_penalty is not None:
            options["repeat_penalty"] = repeat_penalty
        if repeat_last_n is not None:
            options["repeat_last_n"] = repeat_last_n
        if seed is not None:
            options["seed"] = seed

        # Build request
        request_data = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "stream": True
        }

        if system:
            request_data["system"] = system
        if format_json:
            request_data["format"] = "json"
        if options:
            request_data["options"] = options

        logger.info(f"Starting streaming generation with options: {options}")

        try:
            async with self.client.stream(
                "POST",
                "/api/generate",
                json=request_data
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            yield {
                                "response": data.get("response", ""),
                                "done": data.get("done", False),
                                "eval_count": data.get("eval_count"),
                                "eval_duration": data.get("eval_duration")
                            }
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse streaming chunk: {e}")
                            continue

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during streaming: {e}")
            yield {"response": f"Error: {e}", "done": True, "error": True}
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            yield {"response": f"Error: {e}", "done": True, "error": True}


# =============================================================================
# Factory Function
# =============================================================================

def get_ollama_client() -> OllamaClient:
    """
    Factory function to create Ollama client instance

    Returns:
        Configured OllamaClient instance
    """
    settings = get_settings()
    return OllamaClient(settings)

# =============================================================================
# Dependency Injection
# =============================================================================

async def get_ollama_client_dependency() -> OllamaClient:
    """
    FastAPI dependency to get Ollama client

    Returns:
        OllamaClient instance
    """
    client = get_ollama_client()
    async with client:
        yield client