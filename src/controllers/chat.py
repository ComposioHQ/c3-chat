"""Chat event handlers for Chainlit callbacks."""
from typing import Any, Dict, List

import chainlit as cl
from chainlit.logger import logger
from chainlit.types import ThreadDict
from composio_claude import App

from src.api.claude import claude_client
from src.api.composio import composio_integration
import prompts


async def handle_message(message: cl.Message) -> None:
    """
    Handle incoming chat messages from users.
    
    Handles:
    - Managing message history
    - Calling the LLM
    - Processing responses
    - Handling tool use
    - Sending UI messages
    - Updating session state
    
    Args:
        message: The incoming chat message
    """
    logger.info(f"Processing message in thread: {message.thread_id}")

    # Get current user and message history
    user: cl.PersistedUser = cl.user_session.get("user")
    messages = cl.user_session.get("messages")
    tools = cl.user_session.get("tools")
    system_prompt = cl.user_session.get("system_prompt")

    # Add user message to history
    messages.append(
        {"role": "user", "content": [{"type": "text", "text": message.content}]}
    )

    # Call Claude
    response = claude_client.generate_response(messages, system_prompt, tools)

    # Send assistant's text response to UI
    if response.content and response.content[0].type == "text":
        await cl.Message(content=response.content[0].text).send()

    # Update message history based on response type
    if response.stop_reason == "tool_use":
        await _handle_tool_response(user.id, response, messages, tools, system_prompt)
    else:
        # Add regular text response to history
        messages.append(
            {
                "role": response.role,
                "content": [{"type": "text", "text": response.content[0].text}],
            }
        )

    # Update session with new message history
    cl.user_session.set("messages", messages)


async def _handle_tool_response(
    user_id: str, 
    response: Any, 
    messages: List[Dict[str, Any]], 
    tools: List[Dict[str, Any]], 
    system_prompt: str
) -> None:
    """
    Handle a tool response from Claude.
    
    Args:
        user_id: The ID of the user
        response: The Claude response
        messages: The message history
        tools: The available tools
        system_prompt: The system prompt
    """
    # Add assistant's tool use message to history
    messages.append(
        {
            "role": response.role,
            "content": [
                {
                    "type": "tool_use",
                    "id": response.content[-1].id,
                    "name": response.content[-1].name,
                    "input": response.content[-1].input,
                }
            ],
        }
    )

    # Handle tool call
    tool_result = await cl.make_async(composio_integration.handle_tool_call)(user_id, response)

    # Add tool result to message history
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_result["tool_use_id"],
                    "content": tool_result["content"],
                }
            ],
        }
    )

    # Call Claude again with tool results to get final response
    follow_up_response = claude_client.generate_response(messages, system_prompt, tools)

    # Send the follow-up response to UI
    if follow_up_response.content and follow_up_response.content[0].type == "text":
        await cl.Message(content=follow_up_response.content[0].text).send()

    # Add final assistant response to history
    messages.append(
        {
            "role": follow_up_response.role,
            "content": [
                {"type": "text", "text": follow_up_response.content[0].text}
            ],
        }
    )


async def start_chat() -> None:
    """
    Initialize a new chat session.
    
    - Sets up message history
    - Checks for existing connections
    - Prompts for authentication if needed
    """
    user: cl.PersistedUser = cl.user_session.get("user")
    entity = composio_integration.get_entity(user.id)
    logger.info(f"Checking connection for {entity.id}")
    
    # Initialize message history
    cl.user_session.set("messages", [])
    cl.user_session.set("system_prompt", prompts.SYSTEM)
    
    msg = cl.Message(author="Composio", content="")
    
    try:
        # Check if the user has an active GitHub connection
        if composio_integration.check_connection(user.id, App.GITHUB):
            tools = composio_integration.get_tools(apps=[App.GITHUB])
            cl.user_session.set("tools", tools)
        else:
            # Prompt for GitHub authentication
            actions = [
                cl.Action(
                    name="github",
                    payload={"value": "github", "thread_id": msg.thread_id},
                    label="GitHub 💻",
                ),
            ]
            await cl.Message(
                content="Authenticate with GitHub to use GitHub Tools!", actions=actions
            ).send()
    except Exception as e:
        logger.error(f"Error during chat initialization: {str(e)}")
        await cl.Message(content=f"Error initializing chat: {str(e)}").send()


async def resume_chat(thread: ThreadDict) -> None:
    """
    Resume a chat session from an existing thread.
    
    Args:
        thread: The thread to resume
    """
    if "messages" in thread.get("metadata", {}):
        cl.user_session.set("messages", thread["metadata"]["messages"])
    else:
        cl.user_session.set("messages", [])
    
    cl.user_session.set("system_prompt", prompts.SYSTEM) 