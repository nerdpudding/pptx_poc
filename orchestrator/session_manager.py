"""
PPTX POC - Session Manager
In-memory session storage for guided conversation flows
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)

# Session expiry time (1 hour for POC)
SESSION_EXPIRY_HOURS = 1


@dataclass
class ChatMessage:
    """A single message in the conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class PresentationDraft:
    """Draft presentation structure"""
    title: str
    slides: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slides": self.slides
        }


@dataclass
class ConversationSession:
    """A guided conversation session"""
    session_id: str
    template: str
    messages: List[ChatMessage] = field(default_factory=list)
    extracted_info: Dict[str, Any] = field(default_factory=dict)
    draft: Optional[PresentationDraft] = None
    is_ready_for_draft: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str) -> ChatMessage:
        """Add a message to the conversation"""
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)
        self.last_activity = datetime.utcnow()
        return message

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history in format suitable for LLM"""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

    def is_expired(self) -> bool:
        """Check if session has expired"""
        expiry_time = self.last_activity + timedelta(hours=SESSION_EXPIRY_HOURS)
        return datetime.utcnow() > expiry_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "template": self.template,
            "messages": [msg.to_dict() for msg in self.messages],
            "extracted_info": self.extracted_info,
            "draft": self.draft.to_dict() if self.draft else None,
            "is_ready_for_draft": self.is_ready_for_draft,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }


class SessionManager:
    """
    In-memory session manager for guided conversations.
    Thread-safe for concurrent access.
    """

    def __init__(self):
        self._sessions: Dict[str, ConversationSession] = {}
        self._lock = Lock()
        logger.info("SessionManager initialized")

    def create_session(self, template: str) -> ConversationSession:
        """
        Create a new conversation session.

        Args:
            template: The presentation template key (e.g., 'project_init')

        Returns:
            The newly created session
        """
        session_id = str(uuid.uuid4())

        with self._lock:
            # Cleanup old sessions first
            self._cleanup_expired_sessions()

            session = ConversationSession(
                session_id=session_id,
                template=template
            )
            self._sessions[session_id] = session
            logger.info(f"Created session {session_id} for template '{template}'")

        return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get a session by ID.

        Args:
            session_id: The session UUID

        Returns:
            The session if found and not expired, None otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)

            if session is None:
                logger.debug(f"Session {session_id} not found")
                return None

            if session.is_expired():
                logger.info(f"Session {session_id} has expired, removing")
                del self._sessions[session_id]
                return None

            return session

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> Optional[ChatMessage]:
        """
        Add a message to a session.

        Args:
            session_id: The session UUID
            role: Message role ('user' or 'assistant')
            content: Message content

        Returns:
            The created message, or None if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            return None

        with self._lock:
            message = session.add_message(role, content)
            logger.debug(f"Added {role} message to session {session_id}")

        return message

    def update_extracted_info(
        self,
        session_id: str,
        info: Dict[str, Any]
    ) -> bool:
        """
        Update the extracted information for a session.

        Args:
            session_id: The session UUID
            info: Dictionary of extracted information to merge

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            return False

        with self._lock:
            session.extracted_info.update(info)
            session.last_activity = datetime.utcnow()
            logger.debug(f"Updated extracted info for session {session_id}")

        return True

    def set_ready_for_draft(self, session_id: str, ready: bool = True) -> bool:
        """
        Set whether the session is ready for draft generation.

        Args:
            session_id: The session UUID
            ready: Ready status

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            return False

        with self._lock:
            session.is_ready_for_draft = ready
            session.last_activity = datetime.utcnow()

        return True

    def set_draft(
        self,
        session_id: str,
        title: str,
        slides: List[Dict[str, Any]]
    ) -> bool:
        """
        Set the draft presentation for a session.

        Args:
            session_id: The session UUID
            title: Presentation title
            slides: List of slide dictionaries

        Returns:
            True if successful, False if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            return False

        with self._lock:
            session.draft = PresentationDraft(title=title, slides=slides)
            session.last_activity = datetime.utcnow()
            logger.info(f"Set draft for session {session_id}: {len(slides)} slides")

        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: The session UUID

        Returns:
            True if session was deleted, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted session {session_id}")
                return True
            return False

    def get_active_session_count(self) -> int:
        """Get count of active (non-expired) sessions"""
        with self._lock:
            self._cleanup_expired_sessions()
            return len(self._sessions)

    def _cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions. Called internally with lock held.

        Returns:
            Number of sessions removed
        """
        expired_ids = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]

        for sid in expired_ids:
            del self._sessions[sid]

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions")

        return len(expired_ids)


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the singleton session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
