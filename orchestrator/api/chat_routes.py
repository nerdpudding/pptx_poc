"""
PPTX POC - Chat Routes for Guided Mode
Endpoints for AI-guided conversational presentation building
"""

import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from .models import (
    ChatStartRequest,
    ChatStartResponse,
    ChatMessageRequest,
    ChatDraftResponse,
    ChatDraft,
    ChatDraftSlide,
    ChatSessionInfo,
    GenerateResponse,
    PresentationPreview,
    SlidePreview,
    SlideType,
)
from .ollama_client import get_ollama_client
from config import Settings, get_settings
from prompt_loader import get_prompt_loader
from session_manager import get_session_manager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


# =============================================================================
# Chat Session Endpoints
# =============================================================================

@router.post(
    "/start",
    response_model=ChatStartResponse,
    summary="Start guided chat session",
    description="Create a new guided conversation session for a presentation template"
)
async def start_chat_session(
    request: ChatStartRequest,
    settings: Settings = Depends(get_settings)
) -> ChatStartResponse:
    """
    Start a new guided chat session.

    1. Validates template exists and supports guided mode
    2. Creates session in session manager
    3. Returns session ID and AI greeting
    """
    prompt_loader = get_prompt_loader()
    session_manager = get_session_manager()

    # Validate template exists
    template = prompt_loader.get_template(request.template)
    if not template:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "TEMPLATE_NOT_FOUND",
                    "message": f"Template '{request.template}' not found"
                }
            }
        )

    # Check if guided mode is enabled for this template
    guided_config = prompt_loader.get_guided_mode_config(request.template)
    if not guided_config or not guided_config.get("enabled", False):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "GUIDED_MODE_NOT_SUPPORTED",
                    "message": f"Template '{request.template}' does not support guided mode"
                }
            }
        )

    # Create session
    session = session_manager.create_session(request.template)

    # Get greeting message
    greeting = guided_config.get("greeting", "Hello! I'll help you create a presentation. Tell me about your idea.")

    # Add greeting to session as assistant message
    session_manager.add_message(session.session_id, "assistant", greeting)

    logger.info(f"Started chat session {session.session_id} for template '{request.template}'")

    return ChatStartResponse(
        session_id=session.session_id,
        message=greeting
    )


@router.post(
    "/{session_id}/message",
    summary="Send chat message",
    description="Send a message and receive streaming AI response"
)
async def send_chat_message(
    session_id: str,
    request: ChatMessageRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Send a message in a chat session.

    Returns streaming response (SSE) with AI reply.
    Final chunk includes is_ready_for_draft flag.
    """
    session_manager = get_session_manager()
    prompt_loader = get_prompt_loader()

    # Get session
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Session '{session_id}' not found or expired"
                }
            }
        )

    # Add user message to session
    session_manager.add_message(session_id, "user", request.message)

    # Get guided mode config
    guided_config = prompt_loader.get_guided_mode_config(session.template)
    system_prompt = guided_config.get("conversation_system_prompt", "")

    # Build conversation context for LLM
    conversation_history = session.get_conversation_history()

    # Format as a single prompt with conversation history
    history_text = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in conversation_history[:-1]  # All except last (which is current user message)
    ])

    prompt = f"""Previous conversation:
{history_text}

User: {request.message}

Respond naturally as the assistant. Remember to acknowledge what you understand, identify missing information, and make helpful suggestions. Keep responses concise (max 2-3 paragraphs).

When you have gathered all necessary information, end your response with exactly this phrase on its own line:
[READY_FOR_DRAFT]"""

    async def event_generator():
        """Generate SSE events from Ollama stream"""
        ollama_client = get_ollama_client()
        full_response = ""
        is_ready = False

        async with ollama_client:
            async for chunk in ollama_client.stream_generate(
                prompt=prompt,
                system=system_prompt,
                temperature=settings.ollama_temperature,
            ):
                content = chunk.get("response", "")
                done = chunk.get("done", False)

                full_response += content

                # Check for ready marker
                if "[READY_FOR_DRAFT]" in full_response:
                    is_ready = True
                    # Remove marker from response
                    content = content.replace("[READY_FOR_DRAFT]", "").strip()

                # Send chunk
                data = json.dumps({
                    "content": content,
                    "done": done,
                    "is_ready_for_draft": is_ready if done else False
                })
                yield f"data: {data}\n\n"

                if done:
                    # Clean up marker from full response before saving
                    clean_response = full_response.replace("[READY_FOR_DRAFT]", "").strip()

                    # Save assistant response to session
                    session_manager.add_message(session_id, "assistant", clean_response)

                    # Update ready status
                    if is_ready:
                        session_manager.set_ready_for_draft(session_id, True)

                    logger.info(f"Chat message processed for session {session_id}, ready_for_draft={is_ready}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post(
    "/{session_id}/draft",
    response_model=ChatDraftResponse,
    summary="Generate draft from conversation",
    description="Generate a presentation draft based on the conversation"
)
async def generate_draft(
    session_id: str,
    settings: Settings = Depends(get_settings)
) -> ChatDraftResponse:
    """
    Generate draft presentation from conversation.

    Uses conversation history to create structured presentation outline.
    """
    session_manager = get_session_manager()
    prompt_loader = get_prompt_loader()

    # Get session
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Session '{session_id}' not found or expired"
                }
            }
        )

    # Get template info
    template = prompt_loader.get_template(session.template)
    guided_config = prompt_loader.get_guided_mode_config(session.template)

    # Build prompt for draft generation
    conversation_history = session.get_conversation_history()
    history_text = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in conversation_history
    ])

    system_prompt = f"""You are creating a presentation draft based on a conversation.
Use the information gathered to create a structured presentation outline.

Template: {template.name if template else 'General'}
{guided_config.get('required_info', ['Project details']) if guided_config else ''}

Output JSON in this exact format:
{{
  "title": "Presentation Title",
  "slides": [
    {{"type": "title", "heading": "Main Title", "subheading": "Subtitle"}},
    {{"type": "content", "heading": "Section", "bullets": ["Point 1", "Point 2", "Point 3"]}},
    {{"type": "summary", "heading": "Conclusion", "bullets": ["Key takeaway 1", "Key takeaway 2"]}}
  ]
}}"""

    prompt = f"""Based on this conversation, create a presentation draft:

{history_text}

Generate a professional presentation structure with 5-7 slides. Output valid JSON only."""

    try:
        ollama_client = get_ollama_client()
        async with ollama_client:
            # Use non-streaming for draft generation
            presentation = await ollama_client.generate_presentation(
                topic=f"Draft from conversation in session {session_id}",
                language="en",
                slides=5,
                temperature=0.15,
                template=session.template
            )

        # Convert to draft format
        draft_slides = [
            ChatDraftSlide(
                type=slide.type.value,
                heading=slide.heading,
                subheading=slide.subheading,
                bullets=slide.bullets
            )
            for slide in presentation.slides
        ]

        draft = ChatDraft(
            title=presentation.title,
            slides=draft_slides
        )

        # Save draft to session
        session_manager.set_draft(
            session_id,
            draft.title,
            [s.dict() for s in draft_slides]
        )

        logger.info(f"Generated draft for session {session_id}: {len(draft_slides)} slides")

        return ChatDraftResponse(
            session_id=session_id,
            draft=draft
        )

    except Exception as e:
        logger.error(f"Failed to generate draft for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "DRAFT_GENERATION_ERROR",
                    "message": "Failed to generate presentation draft"
                }
            }
        )


@router.post(
    "/{session_id}/generate",
    response_model=GenerateResponse,
    summary="Generate final presentation",
    description="Generate the final presentation from the approved draft"
)
async def generate_from_draft(
    session_id: str,
    settings: Settings = Depends(get_settings)
) -> GenerateResponse:
    """
    Generate final presentation from draft.

    Uses the same generation flow as quick mode.
    """
    import uuid

    session_manager = get_session_manager()

    # Get session
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Session '{session_id}' not found or expired"
                }
            }
        )

    if not session.draft:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "NO_DRAFT",
                    "message": "No draft available. Create a draft first."
                }
            }
        )

    # Generate file ID
    file_id = str(uuid.uuid4())

    # Convert draft to preview format
    preview = PresentationPreview(
        title=session.draft.title,
        slides=[
            SlidePreview(
                type=SlideType(slide["type"]),
                heading=slide["heading"],
                subheading=slide.get("subheading"),
                bullets=slide.get("bullets")
            )
            for slide in session.draft.slides
        ]
    )

    logger.info(f"Generated presentation from draft for session {session_id}")

    return GenerateResponse(
        success=True,
        fileId=file_id,
        downloadUrl=f"/api/v1/download/{file_id}",
        preview=preview
    )


@router.get(
    "/{session_id}",
    response_model=ChatSessionInfo,
    summary="Get session info",
    description="Get information about a chat session"
)
async def get_session_info(session_id: str) -> ChatSessionInfo:
    """Get information about a chat session"""
    session_manager = get_session_manager()

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Session '{session_id}' not found or expired"
                }
            }
        )

    return ChatSessionInfo(
        session_id=session.session_id,
        template=session.template,
        message_count=len(session.messages),
        is_ready_for_draft=session.is_ready_for_draft,
        has_draft=session.draft is not None,
        created_at=session.created_at.isoformat(),
        last_activity=session.last_activity.isoformat()
    )


@router.delete(
    "/{session_id}",
    summary="Delete session",
    description="Delete a chat session"
)
async def delete_session(session_id: str):
    """Delete a chat session"""
    session_manager = get_session_manager()

    if not session_manager.delete_session(session_id):
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Session '{session_id}' not found"
                }
            }
        )

    return {"success": True, "message": f"Session {session_id} deleted"}
