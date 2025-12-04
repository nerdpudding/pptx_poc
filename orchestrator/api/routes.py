"""
PPTX POC - Orchestrator API Routes
API endpoint handlers with proper validation and error handling
"""

import uuid
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from .models import (
    GenerateRequest,
    GenerateResponse,
    ErrorResponse,
    ErrorDetail,
    HealthResponse,
    PresentationPreview,
    SlidePreview,
    SlideType,
)
from config import Settings, get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter()


# =============================================================================
# Health Endpoints
# =============================================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="Returns service health status"
)
async def health_check(
    settings: Settings = Depends(get_settings)
) -> HealthResponse:
    """Health check endpoint for container orchestration"""
    return HealthResponse(
        status="ok",
        service="orchestrator",
        version=settings.app_version
    )


@router.get(
    "/",
    tags=["root"],
    summary="Root endpoint",
    description="Returns basic service information"
)
async def root(settings: Settings = Depends(get_settings)):
    """Root endpoint with service info"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/api/docs"
    }


# =============================================================================
# Generation Endpoints
# =============================================================================

@router.post(
    "/api/v1/generate",
    response_model=GenerateResponse,
    responses={
        200: {"model": GenerateResponse, "description": "Successful generation"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    tags=["generation"],
    summary="Generate presentation",
    description="Generate a PowerPoint presentation from a topic"
)
async def generate_presentation(
    request: GenerateRequest,
    settings: Settings = Depends(get_settings)
) -> GenerateResponse:
    """
    Generate a PowerPoint presentation from the given topic.

    This is currently a placeholder that returns mock data.
    Full implementation will:
    1. Call Ollama to generate content
    2. Send content to pptx-generator
    3. Return file ID and download URL
    """
    logger.info(f"Generate request received: topic='{request.topic}', language='{request.language}'")

    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Create placeholder preview
        # TODO: Replace with actual Ollama-generated content
        preview = PresentationPreview(
            title=request.topic,
            slides=[
                SlidePreview(
                    type=SlideType.TITLE,
                    heading=request.topic,
                    subheading=f"Generated presentation in {request.language}"
                ),
                SlidePreview(
                    type=SlideType.CONTENT,
                    heading="Key Points",
                    bullets=[
                        "This is a placeholder slide",
                        "Ollama integration pending",
                        "Content will be AI-generated"
                    ]
                ),
                SlidePreview(
                    type=SlideType.SUMMARY,
                    heading="Summary",
                    bullets=[
                        "Placeholder implementation",
                        "Ready for Ollama integration"
                    ]
                )
            ]
        )

        return GenerateResponse(
            success=True,
            fileId=file_id,
            downloadUrl=f"/api/v1/download/{file_id}",
            preview=preview
        )

    except Exception as e:
        logger.error(f"Error generating presentation: {e}")
        # Return error response - don't expose internal details
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "GENERATION_ERROR",
                    "message": "Failed to generate presentation. Please try again."
                }
            }
        )


@router.get(
    "/api/v1/download/{file_id}",
    tags=["generation"],
    summary="Download presentation",
    description="Download a generated PowerPoint file"
)
async def download_presentation(file_id: str):
    """
    Download a generated presentation by file ID.

    This is currently a placeholder.
    Full implementation will:
    1. Look up file in storage
    2. Return file as streaming response
    """
    logger.info(f"Download request for file_id: {file_id}")

    # Placeholder - return not implemented status
    return JSONResponse(
        status_code=501,
        content={
            "success": False,
            "error": {
                "code": "NOT_IMPLEMENTED",
                "message": "Download functionality not yet implemented"
            },
            "fileId": file_id
        }
    )
