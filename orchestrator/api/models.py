"""
PPTX POC - Orchestrator API Models
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Language(str, Enum):
    """Supported languages for presentation generation"""
    EN = "en"
    NL = "nl"
    DE = "de"
    FR = "fr"


class SlideType(str, Enum):
    """Types of slides that can be generated"""
    TITLE = "title"
    CONTENT = "content"
    SUMMARY = "summary"


# =============================================================================
# Request Models
# =============================================================================

class GenerateRequest(BaseModel):
    """
    Presentation generation request.
    Matches API contract from PROJECT_PLAN.md
    """
    topic: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The presentation topic",
        examples=["AI in Healthcare", "Introduction to Python"]
    )
    language: Optional[str] = Field(
        default="en",
        max_length=10,
        description="Language for the presentation content",
        examples=["en", "nl", "de"]
    )


# =============================================================================
# Response Models
# =============================================================================

class SlidePreview(BaseModel):
    """Preview of a single slide"""
    type: SlideType
    heading: str
    subheading: Optional[str] = None
    bullets: Optional[list[str]] = None


class PresentationPreview(BaseModel):
    """Preview of the entire presentation"""
    title: str
    slides: list[SlidePreview]


class GenerateResponse(BaseModel):
    """
    Successful generation response.
    Matches API contract from PROJECT_PLAN.md
    """
    success: bool = True
    fileId: str = Field(..., description="Unique identifier for the generated file")
    downloadUrl: str = Field(..., description="URL to download the generated PPTX")
    preview: PresentationPreview = Field(..., description="Preview of slide content")


class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str = Field(..., description="Error code (e.g., VALIDATION_ERROR)")
    message: str = Field(..., description="Human-readable error message")


class ErrorResponse(BaseModel):
    """
    Error response structure.
    Matches API contract from PROJECT_PLAN.md
    """
    success: bool = False
    error: ErrorDetail


# =============================================================================
# Health Check Models
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "ok"
    service: str = "orchestrator"
    version: str


class ServiceStatus(BaseModel):
    """Status of a dependent service"""
    name: str
    status: str
    url: Optional[str] = None


class DetailedHealthResponse(BaseModel):
    """Detailed health check with dependency status"""
    status: str
    service: str
    version: str
    dependencies: list[ServiceStatus]
