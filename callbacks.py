"""Authentication callback functions for Chainlit."""
from typing import Dict, Optional

import chainlit as cl
from chainlit.logger import logger

from config import Config


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    """Handle OAuth callback from providers."""
    logger.info(f"Authenticated with {provider_id}")
    return default_user


@cl.password_auth_callback
def password_auth_callback(username: str, password: str) -> Optional[cl.User]:
    """Handle password authentication."""
    if (username, password) == (Config.ADMIN_USERNAME, Config.ADMIN_PASSWORD):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    return None 