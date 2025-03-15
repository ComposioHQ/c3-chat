"""Claude API client and related functionality."""
import traceback
from typing import Dict, List, Optional, Any

from anthropic import Anthropic
from chainlit.logger import logger

from config import Config


class ClaudeClient:
    """Client for interacting with Claude AI models."""

    def __init__(self):
        """Initialize the Claude client."""
        self.client = Anthropic()
        self.model = Config.CLAUDE_MODEL
        self.max_tokens = Config.CLAUDE_MAX_TOKENS

    def generate_response(
        self, messages: List[Dict[str, Any]], system: str, tools: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """
        Generate a response from Claude based on the provided messages.

        Args:
            messages: The message history to send to Claude
            system: The system prompt to use
            tools: Optional tools to provide to Claude

        Returns:
            The response from Claude
        """
        return self.client.messages.create(
            model=self.model,
            messages=messages,
            system=system,
            tools=tools,
            max_tokens=self.max_tokens,
        )


# Create a singleton instance
claude_client = ClaudeClient() 