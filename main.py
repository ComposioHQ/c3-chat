"""
C3 Chat Application

A Chainlit application that integrates with GitHub through Composio and uses Claude for chat.
"""
import chainlit as cl
from chainlit.logger import logger

# Import callbacks and modules
from callbacks import oauth_callback, password_auth_callback
from src.controllers.actions import connect_github
from src.controllers.chat import handle_message, resume_chat, start_chat
from config import Config


# Register the Chainlit callbacks
cl.on_chat_start(start_chat)
cl.on_message(handle_message)
cl.on_chat_resume(resume_chat)

# Register OAuth callback
cl.oauth_callback(oauth_callback)

# Register password auth callback
cl.password_auth_callback(password_auth_callback)

# Register action callback
cl.action_callback("github")(connect_github)

# Register tool step
cl.step(name="composio_tools", type="tool")


if __name__ == "__main__":
    # Validate configuration
    if not Config.validate():
        logger.error("Invalid configuration. Please check your environment variables.")
        import sys
        sys.exit(1)
    
    logger.info("Starting C3 Chat application manually")
    # This block only runs when main.py is executed directly
    # When using chainlit CLI, this block is not executed 