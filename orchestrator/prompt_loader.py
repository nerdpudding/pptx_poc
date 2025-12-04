"""
PPTX POC - Prompt Loader
Loads and formats prompt templates from YAML configuration
"""

import logging
from pathlib import Path
from functools import lru_cache
from typing import Optional, Dict, Any, List

import yaml

logger = logging.getLogger(__name__)

# Default path to prompts file (relative to this file)
DEFAULT_PROMPTS_PATH = Path(__file__).parent / "prompts.yaml"


class TemplateInfo:
    """Information about a template for API responses"""

    def __init__(self, key: str, data: Dict[str, Any]):
        self.key = key
        self.name = data.get("name", key)
        self.description = data.get("description", "")
        self.system_prompt = data.get("system_prompt", "").strip()
        self.guided_mode = data.get("guided_mode", {})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "guided_mode_enabled": self.guided_mode.get("enabled", False)
        }


class PromptLoader:
    """Loads and manages prompt templates from YAML configuration"""

    def __init__(self, prompts_path: Optional[Path] = None):
        """
        Initialize prompt loader.

        Args:
            prompts_path: Path to prompts.yaml file. Uses default if not provided.
        """
        self.prompts_path = prompts_path or DEFAULT_PROMPTS_PATH
        self._data: Dict[str, Any] = {}
        self._load_prompts()

    def _load_prompts(self) -> None:
        """Load prompts from YAML file"""
        try:
            with open(self.prompts_path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
            logger.info(f"Loaded prompts from {self.prompts_path}")
        except FileNotFoundError:
            logger.error(f"Prompts file not found: {self.prompts_path}")
            self._data = {}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse prompts YAML: {e}")
            self._data = {}

    def reload(self) -> None:
        """Reload prompts from file (useful for development)"""
        self._load_prompts()

    # =========================================================================
    # Defaults
    # =========================================================================

    def get_defaults(self) -> Dict[str, Any]:
        """
        Get default settings for frontend initialization.

        Returns:
            Dictionary with default temperature, slides, language, template
        """
        defaults = self._data.get("defaults", {})
        return {
            "temperature": defaults.get("temperature", 0.15),
            "slides": defaults.get("slides", 5),
            "language": defaults.get("language", "en"),
            "template": defaults.get("template", "general")
        }

    # =========================================================================
    # Templates
    # =========================================================================

    def get_template_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available templates for frontend dropdown.

        Returns:
            List of template info dictionaries with key, name, description, system_prompt
        """
        templates = self._data.get("templates", {})
        result = []
        for key, data in templates.items():
            info = TemplateInfo(key, data)
            result.append(info.to_dict())
        return result

    def get_template(self, template_key: str) -> Optional[TemplateInfo]:
        """
        Get a specific template by key.

        Args:
            template_key: Template identifier (e.g., "general", "project_init")

        Returns:
            TemplateInfo or None if not found
        """
        templates = self._data.get("templates", {})
        if template_key in templates:
            return TemplateInfo(template_key, templates[template_key])
        return None

    def get_system_prompt(self, template_key: str = "general") -> str:
        """
        Get the system prompt for a template.

        Args:
            template_key: Template identifier

        Returns:
            System prompt string
        """
        template = self.get_template(template_key)
        if template:
            return template.system_prompt
        # Fallback
        return "You are a professional presentation designer. Return valid JSON only."

    # =========================================================================
    # Guided Mode
    # =========================================================================

    def get_guided_mode_config(self, template_key: str) -> Optional[Dict[str, Any]]:
        """
        Get guided mode configuration for a template.

        Args:
            template_key: Template identifier

        Returns:
            Guided mode config dict or None if not configured
        """
        templates = self._data.get("templates", {})
        template_data = templates.get(template_key, {})
        guided_mode = template_data.get("guided_mode", {})

        if not guided_mode.get("enabled", False):
            return None

        return {
            "enabled": True,
            "required_info": guided_mode.get("required_info", []),
            "greeting": guided_mode.get("greeting", "").strip(),
            "conversation_system_prompt": guided_mode.get("conversation_system_prompt", "").strip()
        }

    def get_guided_mode_templates(self) -> List[Dict[str, Any]]:
        """
        Get list of templates that support guided mode.

        Returns:
            List of template info for guided mode enabled templates
        """
        templates = self._data.get("templates", {})
        result = []
        for key, data in templates.items():
            guided_mode = data.get("guided_mode", {})
            if guided_mode.get("enabled", False):
                info = TemplateInfo(key, data)
                result.append(info.to_dict())
        return result

    # =========================================================================
    # Prompt Generation
    # =========================================================================

    def get_presentation_prompt(
        self,
        topic: str,
        language: str,
        slides: int,
        template_key: str = "general"
    ) -> str:
        """
        Get formatted presentation generation prompt.

        Args:
            topic: Presentation topic
            language: Target language code
            slides: Number of slides to generate
            template_key: Which template to use

        Returns:
            Formatted prompt string
        """
        templates = self._data.get("templates", {})
        template_data = templates.get(template_key, templates.get("general", {}))
        template = template_data.get("presentation_prompt", "")

        if not template:
            logger.warning(f"No prompt template found for '{template_key}', using fallback")
            return self._fallback_presentation_prompt(topic, language, slides)

        # Format the template with variables
        try:
            return template.format(
                topic=topic,
                language=language,
                slides=slides,
                slides_minus_1=slides - 1
            ).strip()
        except KeyError as e:
            logger.error(f"Missing variable in prompt template: {e}")
            return self._fallback_presentation_prompt(topic, language, slides)

    def _fallback_presentation_prompt(
        self,
        topic: str,
        language: str,
        slides: int
    ) -> str:
        """
        Fallback prompt if YAML loading fails.
        This ensures the system still works even with config issues.
        """
        return f"""Generate a professional PowerPoint presentation in {language} about: "{topic}"

Return ONLY valid JSON with exactly {slides} slides:
{{
    "title": "Presentation title",
    "slides": [
        {{"type": "title|content|summary", "heading": "...", "subheading": "...", "bullets": [...]}}
    ]
}}

Slide 1: title slide
Slides 2-{slides - 1}: content slides
Slide {slides}: summary slide"""


# =============================================================================
# Cached Instance
# =============================================================================

@lru_cache()
def get_prompt_loader() -> PromptLoader:
    """
    Get cached prompt loader instance.
    Uses lru_cache to avoid reloading YAML on every request.
    """
    return PromptLoader()
