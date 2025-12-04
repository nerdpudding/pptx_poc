# Guided Mode - AI-Guided Presentation Builder

> **Sprint 1 Feature Requirement**
> **Priority:** Must Have for POC
> **Status:** In Development

---

## Executive Summary

Add an AI-guided conversational flow that helps users create structured presentations through a step-by-step interview process. Users with unstructured ideas can describe them naturally, and the AI guides them to create proper presentations (like PIDs, POC demos, etc.).

---

## User Stories

### US1: Select Guided Mode
> As a user, I want to choose between "Quick Mode" and "Guided Mode" so that I can either quickly generate a presentation or get AI assistance in structuring my idea.

**Acceptance Criteria:**
- [ ] Mode toggle visible on main page
- [ ] Default mode is Quick Mode (current behavior)
- [ ] Switching modes changes the visible UI

### US2: Start Guided Conversation
> As a user, I want to select a presentation type and start a guided session so that the AI knows what kind of presentation to help me create.

**Acceptance Criteria:**
- [ ] Template dropdown works in Guided Mode
- [ ] Starting session shows AI greeting specific to template
- [ ] AI asks user to describe their idea

### US3: Natural Language Input
> As a user, I want to describe my idea in my own words (unstructured) so that I don't need to know the required format upfront.

**Acceptance Criteria:**
- [ ] User can type free-form text
- [ ] AI extracts relevant information from natural language
- [ ] AI acknowledges what it understood

### US4: AI-Guided Information Gathering
> As a user, I want the AI to ask me clarifying questions about missing information so that I provide everything needed for a complete presentation.

**Acceptance Criteria:**
- [ ] AI identifies missing required information
- [ ] AI asks follow-up questions conversationally (not as interrogation)
- [ ] AI makes suggestions where appropriate

### US5: Create Draft Preview
> As a user, I want to preview the presentation structure before final generation so that I can review and request changes.

**Acceptance Criteria:**
- [ ] "Create Draft" button appears when AI has enough info
- [ ] Draft shows slide titles and bullet points
- [ ] User can see full structure before committing

### US6: Refine Through Conversation
> As a user, I want to continue chatting to refine the draft so that I can make changes without starting over.

**Acceptance Criteria:**
- [ ] User can request changes via chat after draft
- [ ] AI updates understanding based on feedback
- [ ] New draft can be generated with changes

### US7: Generate Final Presentation
> As a user, I want to generate the final presentation from the approved draft so that I get a downloadable result.

**Acceptance Criteria:**
- [ ] "Generate Presentation" button creates final output
- [ ] Output quality matches Quick Mode
- [ ] Download link provided

---

## Functional Requirements

### FR1: Mode Selection
| ID | Requirement |
|----|-------------|
| FR1.1 | System shall provide toggle between Quick Mode and Guided Mode |
| FR1.2 | Quick Mode shall maintain existing behavior |
| FR1.3 | Guided Mode shall show chat interface |

### FR2: Session Management
| ID | Requirement |
|----|-------------|
| FR2.1 | System shall create unique session ID for each conversation |
| FR2.2 | Session shall persist conversation history in memory |
| FR2.3 | Session shall track extracted information |
| FR2.4 | Sessions shall auto-expire after 1 hour of inactivity |

### FR3: Conversation Flow
| ID | Requirement |
|----|-------------|
| FR3.1 | AI shall greet user with template-specific introduction |
| FR3.2 | AI shall extract information from natural language input |
| FR3.3 | AI shall identify and ask about missing required information |
| FR3.4 | AI shall make suggestions and recommendations |
| FR3.5 | AI shall indicate when ready to create draft |

### FR4: Draft Generation
| ID | Requirement |
|----|-------------|
| FR4.1 | System shall generate draft from conversation context |
| FR4.2 | Draft shall show presentation structure preview |
| FR4.3 | User shall be able to request draft regeneration |

### FR5: Final Generation
| ID | Requirement |
|----|-------------|
| FR5.1 | System shall generate presentation from approved draft |
| FR5.2 | Generation shall use same quality as Quick Mode |
| FR5.3 | Download URL shall be provided |

---

## Non-Functional Requirements

### NFR1: Performance
- Chat response streaming shall start within 2 seconds
- Session lookup shall complete within 100ms

### NFR2: Scalability (POC Scope)
- In-memory session storage (no database required)
- Single-instance deployment sufficient

### NFR3: Usability
- Chat interface shall be intuitive (message bubbles)
- AI responses shall be concise (max 2-3 paragraphs)
- Streaming shall provide real-time feedback

---

## Technical Specifications

### API Endpoints

#### POST /api/v1/chat/start
Start a new guided session.

**Request:**
```json
{
  "template": "project_init"
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "message": "AI greeting message..."
}
```

#### POST /api/v1/chat/{session_id}/message
Send message and receive streaming response.

**Request:**
```json
{
  "message": "User's message text"
}
```

**Response:** Server-Sent Events (SSE)
```
data: {"content": "AI response chunk", "done": false}
data: {"content": " more text", "done": false}
data: {"content": "", "done": true, "is_ready_for_draft": false}
```

#### POST /api/v1/chat/{session_id}/draft
Generate draft from conversation.

**Response:**
```json
{
  "session_id": "uuid",
  "draft": {
    "title": "Presentation Title",
    "slides": [
      {
        "type": "title",
        "heading": "...",
        "subheading": "...",
        "bullets": null
      }
    ]
  }
}
```

#### POST /api/v1/chat/{session_id}/generate
Generate final presentation from draft.

**Response:**
```json
{
  "success": true,
  "fileId": "uuid",
  "downloadUrl": "/api/v1/download/uuid",
  "preview": { ... }
}
```

### Data Models

```python
class ChatMessage:
    role: str        # "user" | "assistant"
    content: str
    timestamp: datetime

class ConversationSession:
    session_id: str
    template: str
    messages: list[ChatMessage]
    extracted_info: dict
    draft: Optional[PresentationContent]
    created_at: datetime
```

### Prompt Configuration

Each template supporting guided mode includes:
```yaml
guided_mode:
  enabled: true
  required_info: [list of required information]
  greeting: "Template-specific greeting"
  conversation_system_prompt: "System prompt for conversation"
```

---

## UI/UX Design

### Mode Toggle
```
[Quick Mode] [Guided Mode]
     ^active
```

### Chat Interface
```
+----------------------------------+
| Template: [Project Initiation ▼] |
+----------------------------------+
|                                  |
|  [AI] Hi! I'll help you create   |
|  a PID. Tell me about your idea. |
|                                  |
|  [User] I want to build an app   |
|  that helps people...            |
|                                  |
|  [AI] That sounds interesting!   |
|  So you want to... Let me ask... |
|                                  |
+----------------------------------+
| [Type your message...        ] ↵ |
+----------------------------------+
| [Create Draft]  [Generate]       |
+----------------------------------+
```

---

## Implementation Checklist

### Backend
- [ ] Create `session_manager.py`
- [ ] Add chat models to `models.py`
- [ ] Create `chat_routes.py`
- [ ] Include routes in `main.py`
- [ ] Add `guided_mode` to `prompts.yaml`
- [ ] Update `prompt_loader.py`

### Frontend
- [ ] Add mode toggle to `index.html`
- [ ] Add chat container to `index.html`
- [ ] Add chat styles to `style.css`
- [ ] Implement chat logic in `app.js`
- [ ] Wire up streaming responses
- [ ] Add draft preview display

### Testing
- [ ] Test session creation
- [ ] Test message exchange
- [ ] Test streaming responses
- [ ] Test draft generation
- [ ] Test final generation
- [ ] End-to-end user flow test

---

## Out of Scope (Future Enhancements)

- Database persistence for conversations
- User authentication
- Conversation history across sessions
- Multiple concurrent drafts
- Collaborative editing
- Custom template creation by users

---

## Success Metrics

| Metric | Target |
|--------|--------|
| User can complete guided flow | Yes |
| Conversation feels natural | Subjective - user feedback |
| Draft matches conversation | Information extracted correctly |
| Final output quality | Same as Quick Mode |

---

*Document Version: 1.0*
*Last Updated: 2025-12-04*
*Author: Claude Code*
