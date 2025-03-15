"""Configuration settings for the C3 Chat application."""
import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration settings loaded from environment variables."""

    # Claude API settings
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    CLAUDE_MAX_TOKENS: int = int(os.getenv("CLAUDE_MAX_TOKENS", "1000"))

    # GitHub OAuth settings
    GITHUB_CLIENT_ID: Optional[str] = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: Optional[str] = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI: str = os.getenv(
        "GITHUB_REDIRECT_URI", "https://usefulagents.com/redirect"
    )

    # Deployment settings
    RAILWAY_PUBLIC_DOMAIN: Optional[str] = os.getenv("RAILWAY_PUBLIC_DOMAIN")

    # Auth settings
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin")

    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is set."""
        required_vars = ["GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "RAILWAY_PUBLIC_DOMAIN"]
        
        missing_vars = [var for var in required_vars if getattr(cls, var) is None]
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
            
        return True 