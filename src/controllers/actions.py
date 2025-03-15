"""Action handlers for Chainlit callbacks."""
import chainlit as cl
from chainlit.logger import logger
from composio_claude import App

from src.api.composio import composio_integration
from config import Config


@cl.action_callback("github")
async def connect_github(action: cl.Action) -> None:
    """
    Handle GitHub connection action.
    
    Args:
        action: The action to handle
    """
    railway_domain = Config.RAILWAY_PUBLIC_DOMAIN
    app_name = action.payload.get("value")
    thread_id = action.payload.get("thread_id")
    
    if not railway_domain:
        await cl.Message(
            content="Error: Missing RAILWAY_PUBLIC_DOMAIN environment variable"
        ).send()
        return
        
    user: cl.PersistedUser = cl.user_session.get("user")
    
    try:
        # Initiate the connection
        conn_req = composio_integration.initiate_connection(
            user.id, app_name, thread_id, railway_domain
        )
        
        # Send the redirect URL to the user
        await cl.Message(content=f"Click [here]({conn_req.redirectUrl}) to connect!").send()
        
        # Get the tools and store them in the session
        tools = composio_integration.get_tools(apps=[App.GITHUB])
        cl.user_session.set("tools", tools)
    except Exception as e:
        logger.error(f"Error connecting to GitHub: {str(e)}")
        await cl.Message(
            content=f"Error connecting to GitHub: {str(e)}"
        ).send() 