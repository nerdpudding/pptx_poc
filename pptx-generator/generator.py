#!/usr/bin/env python3
"""
PPTX POC - PPTX Generator Service
FastAPI service for PowerPoint file generation using python-pptx
"""

import os
import uuid
import logging
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from slide_builder import SlideBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

APP_VERSION = "0.1.0"
OUTPUT_DIR = "/app/output"
TEMPLATE_PATH = "/app/templates/default.pptx"


# =============================================================================
# Models
# =============================================================================

class SlideType(str, Enum):
    """Types of slides that can be generated"""
    TITLE = "title"
    CONTENT = "content"
    SUMMARY = "summary"


class SlideContent(BaseModel):
    """Content for a single slide"""
    type: SlideType
    heading: str = Field(..., min_length=1, max_length=200)
    subheading: Optional[str] = Field(default=None, max_length=300)
    bullets: Optional[list[str]] = Field(default=None, max_items=10)


class PresentationContent(BaseModel):
    """Full presentation content structure"""
    title: str = Field(..., min_length=1, max_length=200)
    slides: list[SlideContent] = Field(..., min_length=1, max_length=20)


class GenerateRequest(BaseModel):
    """PPTX generation request model"""
    content: PresentationContent
    template: Optional[str] = Field(default="basic", max_length=50)
    filename: Optional[str] = Field(default="presentation.pptx", max_length=100)


class GenerateResponse(BaseModel):
    """PPTX generation response"""
    success: bool
    file_id: str
    filename: str
    message: str


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str
    version: str


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: dict


# =============================================================================
# Application
# =============================================================================

app = FastAPI(
    title="PPTX Generator API",
    description="PowerPoint generation service using python-pptx",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# =============================================================================
# Endpoints
# =============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check"
)
async def health_check() -> HealthResponse:
    """Health check endpoint for container orchestration"""
    return HealthResponse(
        status="ok",
        service="pptx-generator",
        version=APP_VERSION
    )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with service info"""
    return {
        "service": "PPTX Generator",
        "version": APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.post(
    "/generate",
    response_model=GenerateResponse,
    responses={
        200: {"model": GenerateResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    tags=["generation"],
    summary="Generate PPTX file"
)
async def generate_pptx(request: GenerateRequest) -> GenerateResponse:
    """
    Generate a PowerPoint file from structured content.

    Creates a real PPTX file using python-pptx with professional styling.
    Supports any number of slides with title, content, and summary types.
    """
    logger.info(f"Generate request: title='{request.content.title}', slides={len(request.content.slides)}")

    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_path = os.path.join(OUTPUT_DIR, f"{file_id}.pptx")

        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Create presentation using SlideBuilder
        builder = SlideBuilder(template_path=TEMPLATE_PATH)

        # Process each slide from the request
        for slide in request.content.slides:
            builder.add_slide_by_type(
                slide_type=slide.type.value,
                heading=slide.heading,
                subheading=slide.subheading,
                bullets=slide.bullets
            )

        # Save the presentation
        builder.save(file_path)

        logger.info(f"PPTX generated successfully: {file_id} ({builder.slide_count} slides)")

        return GenerateResponse(
            success=True,
            file_id=file_id,
            filename=request.filename,
            message=f"PPTX generated with {builder.slide_count} slides"
        )

    except Exception as e:
        logger.error(f"Error generating PPTX: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "GENERATION_ERROR",
                    "message": f"Failed to generate PPTX file: {str(e)}"
                }
            }
        )


@app.get(
    "/download/{file_id}",
    tags=["download"],
    summary="Download PPTX file",
    responses={
        200: {"description": "PPTX file download"},
        404: {"model": ErrorResponse},
    }
)
async def download_pptx(file_id: str, filename: Optional[str] = "presentation.pptx"):
    """
    Download a generated PPTX file by ID.

    Args:
        file_id: Unique identifier for the generated file
        filename: Optional filename for the download (default: presentation.pptx)

    Returns:
        FileResponse with the PPTX file
    """
    logger.info(f"Download request for file_id: {file_id}")

    # Validate file_id format (UUID)
    try:
        uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_FILE_ID",
                    "message": "Invalid file ID format"
                }
            }
        )

    file_path = os.path.join(OUTPUT_DIR, f"{file_id}.pptx")

    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "FILE_NOT_FOUND",
                    "message": "The requested file does not exist or has expired"
                },
                "file_id": file_id
            }
        )

    logger.info(f"Serving file: {file_path}")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "generator:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
