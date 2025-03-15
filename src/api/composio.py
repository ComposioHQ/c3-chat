"""Composio API integrations and related functionality."""
import traceback
from typing import Any, Dict, List, Optional

import chainlit as cl
from chainlit.logger import logger
from composio.exceptions import NoItemsFound
from composio_claude import App, ComposioToolSet

from config import Config


class ComposioIntegration:
    """Manager for Composio integrations and tools."""

    def __init__(self):
        """Initialize the Composio integration manager."""
        self.toolset = ComposioToolSet()
    
    def get_entity(self, user_id: str) -> Any:
        """Get or create a Composio entity for the given user."""
        return self.toolset.get_entity(user_id)
    
    def get_tools(self, apps: List[App]) -> List[Dict[str, Any]]:
        """Get tools for the specified apps."""
        return self.toolset.get_tools(apps=apps)
    
    def check_connection(self, user_id: str, app: App) -> bool:
        """
        Check if a user has an active connection to the specified app.
        
        Args:
            user_id: The user ID to check
            app: The app to check connection for
            
        Returns:
            True if connected, False otherwise
        """
        entity = self.get_entity(user_id)
        try:
            connection = entity.get_connection(app=app)
            logger.info(f"{entity.id} has connection status: {connection.status}")
            return connection.status == "ACTIVE"
        except NoItemsFound:
            logger.info(f"No connection found for {entity.id} to {app.name}")
            return False
    
    def create_integration_if_not_exists(self, app: App) -> Any:
        """
        Create an integration if one doesn't exist for the specified app.
        
        Args:
            app: The app to create an integration for
            
        Returns:
            The integration object
        """
        integrations = self.toolset.get_integrations(app=app)
        if not integrations:
            logger.info(f"[!] Integration not found for {app.name}. Creating new integration")
            integration_obj = self.toolset.create_integration(
                app=app,
                auth_mode="OAUTH2",
                use_composio_oauth_app=False,
                force_new_integration=True,
                auth_config={
                    "client_id": Config.GITHUB_CLIENT_ID,
                    "client_secret": Config.GITHUB_CLIENT_SECRET,
                    "redirect_uri": Config.GITHUB_REDIRECT_URI,
                },
            )
            return integration_obj
        
        logger.info(f"[!] Integration ID: {integrations[0].id} found for {app.name}")
        return integrations[0]
    
    def initiate_connection(
        self, user_id: str, app_name: str, thread_id: str, railway_domain: str
    ) -> Any:
        """
        Initiate a connection to the specified app.
        
        Args:
            user_id: The user ID to create a connection for
            app_name: The name of the app to connect to
            thread_id: The thread ID for the redirect URL
            railway_domain: The domain for the redirect URL
            
        Returns:
            The connection request object
        """
        entity = self.get_entity(user_id)
        app_enum = getattr(App, app_name)
        redirect_url = f"https://{railway_domain}/threads/{thread_id}"
        
        integration = self.create_integration_if_not_exists(app_enum)
        logger.info(f"Initiating connection for {entity.id}")
        logger.info(f"Redirect URL: {redirect_url}")
        
        return entity.initiate_connection(
            app_name,
            auth_mode="OAUTH2",
            integration=integration,
            use_composio_auth=False,
            redirect_url=redirect_url,
        )
    
    def handle_tool_call(self, user_id: str, response: Any) -> Dict[str, str]:
        """
        Handle a tool call from a Claude response.
        
        Args:
            user_id: The ID of the user making the request
            response: The Claude response containing tool calls
            
        Returns:
            A dictionary with the tool use ID and content
        """
        tool_use_id = response.content[-1].id
        logger.info(f"Handling tool call with ID: {tool_use_id}")
        
        try:
            tool_call_response = self.toolset.handle_tool_calls(response, entity_id=user_id)
            logger.info("Tool call handled successfully")
            return {"tool_use_id": tool_use_id, "content": str(tool_call_response)}
        except Exception as e:
            logger.error(f"Error handling tool call: {str(e)}")
            logger.error(traceback.format_exc())
            return {"tool_use_id": tool_use_id, "content": f"Error: {str(e)}"}


# Create a singleton instance
composio_integration = ComposioIntegration() 