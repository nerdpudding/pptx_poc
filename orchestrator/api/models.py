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

    # Ollama parameters (optional, uses server defaults if not provided)
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0-2.0). Lower = more consistent, higher = more creative"
    )
    num_ctx: Optional[int] = Field(
        default=None,
        ge=65536,
        le=262144,
        description="Context window size (64K-256K). Currently disabled - uses modelfile default"
    )
    slides: Optional[int] = Field(
        default=None,
        ge=3,
        le=10,
        description="Number of slides to generate (3-10)"
    )
    template: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Template key (e.g., 'general', 'project_init', 'poc_demo')"
    )
    system: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Custom system prompt to override template default"
    )


class StreamRequest(BaseModel):
    """
    Streaming test/debug request with full Ollama parameter control.
    Used for testing and debugging LLM output.
    """
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The prompt to send to Ollama"
    )
    system: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="System message (overrides default)"
    )

    # Sampling parameters
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0-2.0)"
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Top-K sampling (1-100)"
    )
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Top-P / nucleus sampling (0.0-1.0)"
    )
    min_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Min-P sampling (0.0-1.0)"
    )

    # Output control
    num_ctx: Optional[int] = Field(
        default=None,
        ge=65536,
        le=262144,
        description="Context window size (64K-256K)"
    )
    num_predict: Optional[int] = Field(
        default=None,
        ge=-1,
        le=16384,
        description="Max tokens to generate (-1 = infinite)"
    )

    # Repetition control
    repeat_penalty: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Repetition penalty (1.0 = no penalty)"
    )
    repeat_last_n: Optional[int] = Field(
        default=None,
        ge=-1,
        le=4096,
        description="Tokens to look back for repetition (-1 = num_ctx)"
    )

    # Other
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )
    format_json: Optional[bool] = Field(
        default=False,
        description="Force JSON output format"
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
