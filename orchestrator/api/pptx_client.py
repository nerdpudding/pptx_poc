#!/usr/bin/env python3
"""
PPTX POC - PPTX Generator Client
Async HTTP client for PPTX Generator service
"""

import logging
from typing import Optional, Dict, Any, List

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

from config import Settings, get_settings

logger = logging.getLogger(__name__)


# =============================================================================
# Models
# =============================================================================

class SlideRequest(BaseModel):
    """Single slide content for PPTX generation request"""
    type: str  # "title", "content", "summary"
    heading: str
    subheading: Optional[str] = None
    bullets: Optional[List[str]] = None


class PresentationRequest(BaseModel):
    """Full presentation content for PPTX generation"""
    title: str
    slides: List[SlideRequest]


class GenerateRequest(BaseModel):
    """PPTX generation request model"""
    content: PresentationRequest
    template: str = "basic"
    filename: str = "presentation.pptx"


class GenerateResponse(BaseModel):
    """PPTX generation response model"""
    success: bool
    file_id: str
    filename: str
    message: str


# =============================================================================
# PPTX Generator Client Class
# =============================================================================

class PPTXGeneratorClient:
    """Async HTTP client for PPTX Generator service"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.pptx_generator_url.rstrip('/')
        self.timeout = httpx.Timeout(settings.pptx_generator_timeout)
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def generate(
        self,
        title: str,
        slides: List[Dict[str, Any]],
        template: str = "basic",
        filename: str = "presentation.pptx"
    ) -> GenerateResponse:
        """
        Generate a PPTX file from slide content.

        Args:
            title: Presentation title
            slides: List of slide dictionaries with type, heading, subheading, bullets
            template: Template name (default: "basic")
            filename: Output filename (default: "presentation.pptx")

        Returns:
            GenerateResponse with file_id for download

        Raises:
            HTTPException: If generation fails
        """
        logger.info(f"Generating PPTX: title='{title}', slides={len(slides)}")

        # Build request
        request_data = GenerateRequest(
            content=PresentationRequest(
                title=title,
                slides=[SlideRequest(**s) for s in slides]
            ),
            template=template,
            filename=filename
        )

        try:
            response = await self.client.post(
                "/generate",
                json=request_data.model_dump()
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"PPTX generated: file_id={data.get('file_id')}")

            return GenerateResponse(**data)

        except RetryError as e:
            logger.error(f"PPTX generation failed after retries: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error": {
                        "code": "PPTX_SERVICE_UNAVAILABLE",
                        "message": "PPTX Generator service is unavailable. Please try again."
                    }
                }
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"PPTX generation HTTP error: {e}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail={
                    "success": False,
                    "error": {
                        "code": "PPTX_GENERATION_ERROR",
                        "message": f"Failed to generate PPTX: {e.response.text}"
                    }
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error generating PPTX: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": {
                        "code": "PPTX_ERROR",
                        "message": "Failed to generate PPTX file."
                    }
                }
            )

    async def health_check(self) -> bool:
        """Check if PPTX Generator service is healthy"""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"PPTX Generator health check failed: {e}")
            return False


# =============================================================================
# Factory Function
# =============================================================================

def get_pptx_client() -> PPTXGeneratorClient:
    """
    Factory function to create PPTX Generator client instance.

    Returns:
        Configured PPTXGeneratorClient instance
    """
    settings = get_settings()
    return PPTXGeneratorClient(settings)


# =============================================================================
# Dependency Injection
# =============================================================================

async def get_pptx_client_dependency() -> PPTXGeneratorClient:
    """
    FastAPI dependency to get PPTX Generator client.

    Yields:
        PPTXGeneratorClient instance
    """
    client = get_pptx_client()
    async with client:
        yield client
