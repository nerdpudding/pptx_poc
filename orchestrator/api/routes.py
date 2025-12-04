"""
PPTX POC - Orchestrator API Routes
API endpoint handlers with proper validation and error handling
"""

import uuid
import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from .models import (
    GenerateRequest,
    GenerateResponse,
    ErrorResponse,
    ErrorDetail,
    HealthResponse,
    PresentationPreview,
    SlidePreview,
    SlideType,
    StreamRequest,
)
from .ollama_client import OllamaClient, get_ollama_client
from config import Settings, get_settings
from prompt_loader import get_prompt_loader

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
# Configuration Endpoints
# =============================================================================

@router.get(
    "/api/v1/config",
    tags=["config"],
    summary="Get configuration",
    description="Returns default settings and available templates for frontend initialization"
)
async def get_config():
    """
    Get configuration for frontend initialization.

    Returns:
        - defaults: Default settings (temperature, slides, language, template)
        - templates: List of available templates with their system prompts
    """
    prompt_loader = get_prompt_loader()

    return {
        "defaults": prompt_loader.get_defaults(),
        "templates": prompt_loader.get_template_list()
    }


@router.get(
    "/api/v1/templates",
    tags=["config"],
    summary="Get available templates",
    description="Returns list of available presentation templates"
)
async def get_templates():
    """
    Get list of available presentation templates.

    Returns:
        List of templates with key, name, description, and system_prompt
    """
    prompt_loader = get_prompt_loader()
    return {"templates": prompt_loader.get_template_list()}


@router.get(
    "/api/v1/templates/{template_key}",
    tags=["config"],
    summary="Get specific template",
    description="Returns details for a specific template"
)
async def get_template(template_key: str):
    """
    Get details for a specific template.

    Args:
        template_key: Template identifier (e.g., "general", "project_init")

    Returns:
        Template details including system_prompt
    """
    prompt_loader = get_prompt_loader()
    template = prompt_loader.get_template(template_key)

    if not template:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "TEMPLATE_NOT_FOUND",
                    "message": f"Template '{template_key}' not found"
                }
            }
        )

    return template.to_dict()


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

    1. Calls Ollama to generate presentation content
    2. Returns file ID and download URL with preview
    """
    # Get defaults from YAML config
    prompt_loader = get_prompt_loader()
    defaults = prompt_loader.get_defaults()

    # Use provided values or defaults (YAML defaults > config.py defaults)
    effective_slides = request.slides if request.slides is not None else defaults.get("slides", settings.default_slides)
    effective_temp = request.temperature if request.temperature is not None else defaults.get("temperature", settings.ollama_temperature)
    effective_ctx = request.num_ctx if request.num_ctx is not None else settings.ollama_num_ctx
    effective_template = request.template if request.template is not None else defaults.get("template", "general")

    logger.info(
        f"Generate request received: topic='{request.topic}', "
        f"language='{request.language}', slides={effective_slides}, "
        f"temperature={effective_temp}, template='{effective_template}'"
    )

    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Call Ollama to generate presentation content
        ollama_client = get_ollama_client()
        async with ollama_client:
            presentation_content = await ollama_client.generate_presentation(
                topic=request.topic,
                language=request.language or "en",
                slides=effective_slides,
                temperature=effective_temp,
                num_ctx=effective_ctx,
                template=effective_template,
                system_prompt=request.system  # User override for system prompt
            )

        # Convert Ollama response to preview format
        preview = PresentationPreview(
            title=presentation_content.title,
            slides=[
                SlidePreview(
                    type=SlideType(slide.type.value),
                    heading=slide.heading,
                    subheading=slide.subheading,
                    bullets=slide.bullets
                )
                for slide in presentation_content.slides
            ]
        )

        logger.info(f"Successfully generated presentation with {len(preview.slides)} slides")

        return GenerateResponse(
            success=True,
            fileId=file_id,
            downloadUrl=f"/api/v1/download/{file_id}",
            preview=preview
        )

    except HTTPException:
        # Re-raise HTTP exceptions (from ollama_client)
        raise
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


# =============================================================================
# Streaming/Debug Endpoints
# =============================================================================

@router.post(
    "/api/v1/stream",
    tags=["debug"],
    summary="Stream LLM output",
    description="Stream raw LLM output for testing and debugging. Returns Server-Sent Events."
)
async def stream_generate(
    request: StreamRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Stream raw LLM output via Server-Sent Events.
    Useful for testing prompts and debugging Ollama integration.
    """
    logger.info(f"Stream request: prompt length={len(request.prompt)}, system={'yes' if request.system else 'no'}")

    async def event_generator():
        """Generate SSE events from Ollama stream"""
        ollama_client = get_ollama_client()
        async with ollama_client:
            async for chunk in ollama_client.stream_generate(
                prompt=request.prompt,
                system=request.system,
                temperature=request.temperature,
                num_ctx=request.num_ctx,
                num_predict=request.num_predict,
                top_k=request.top_k,
                top_p=request.top_p,
                min_p=request.min_p,
                repeat_penalty=request.repeat_penalty,
                repeat_last_n=request.repeat_last_n,
                seed=request.seed,
                format_json=request.format_json or False
            ):
                # Format as SSE
                data = json.dumps(chunk)
                yield f"data: {data}\n\n"

                # If done, send final event
                if chunk.get("done"):
                    yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
