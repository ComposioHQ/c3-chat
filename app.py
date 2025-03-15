import traceback
from typing import Dict, Optional

from anthropic import Anthropic
import chainlit as cl
from chainlit.types import ThreadDict
from chainlit.logger import logger
from composio_claude import Action, App, ComposioToolSet
from composio.exceptions import NoItemsFound
from dotenv import load_dotenv
import os
import prompts

load_dotenv()

anthropic_client = Anthropic()
toolset = ComposioToolSet()


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    logger.info(f"Authenticated with {provider_id}")
    return default_user


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("admin", "admin"):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None


def create_integration_if_not_exists(app) -> str:
    integrations = toolset.get_integrations(app=app)
    if not integrations:
        logger.info("[!] Integration not found. Creating new integration")
        integration_obj = toolset.create_integration(
            app=app,
            auth_mode="OAUTH2",
            use_composio_oauth_app=False,
            force_new_integration=True,
            auth_config={
                "client_id": os.getenv("GITHUB_CLIENT_ID"),
                "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
                "redirect_uri": "https://usefulagents.com/redirect",
            },
        )
        return integration_obj
    logger.info(f"[!] Integration ID: {integrations[0].id} found.")
    return integrations[0]


@cl.action_callback("github")
async def connect_github(action: cl.Action):
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    app_name = action.payload.get("value")
    thread_id = action.payload.get("thread_id")
    app_enum = getattr(App, app_name)
    user: cl.PersistedUser = cl.user_session.get("user")
    entity = toolset.get_entity(user.id)

    redirect_url = f"https://{railway_domain}/threads/{thread_id}"
    integration = create_integration_if_not_exists(app_enum)
    logger.info(f"Initiating connection for {entity.id}")
    logger.info(f"Redirect URL: {redirect_url}")

    conn_req = entity.initiate_connection(
        app_name,
        auth_mode="OAUTH2",
        integration=integration,
        use_composio_auth=False,
        redirect_url=redirect_url,
    )
    await cl.Message(content=f"Click [here]({conn_req.redirectUrl}) to connect!").send()
    tools = toolset.get_tools(apps=[App.GITHUB])
    cl.user_session.set("tools", tools)


@cl.on_chat_start
async def start_chat():
    user: cl.PersistedUser = cl.user_session.get("user")
    entity = toolset.get_entity(user.id)
    logger.info(f"Checking connection for {entity.id}")
    msg = cl.Message(author="Composio", content="")
    try:
        connected_account = entity.get_connection(app=App.GITHUB)
        logger.info(f"{entity.id} has connection status: {connected_account.status}")
        tools = toolset.get_tools(apps=[App.GITHUB])
        cl.user_session.set("tools", tools)
    except NoItemsFound:
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
    cl.user_session.set("messages", [])


def call_claude(messages, tools=None):
    """
    Makes a call to the Claude API and returns the response.

    This function is solely responsible for making the API call, not handling
    message management or UI updates.

    Args:
        messages: The message history to send to Claude
        tools: Optional tools to provide to Claude

    Returns:
        The response from Claude
    """
    return anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=messages,
        system=prompts.SYSTEM,
        tools=tools,
        max_tokens=1000,
    )


cl.step(name="composio_tools", type="tool")


async def handle_tool_call(user_id, response):
    """
    Handles tool calls from the Claude response.

    Args:
        user_id: The ID of the user making the request
        response: The Claude response containing tool calls

    Returns:
        The result of the tool call
    """
    tool_use_id = response.content[-1].id
    logger.info(f"Handling tool call with ID: {tool_use_id}")

    try:
        tool_call_response = toolset.handle_tool_calls(response, entity_id=user_id)
        logger.info("Tool call handled successfully")
        return {"tool_use_id": tool_use_id, "content": str(tool_call_response)}
    except Exception as e:
        logger.error(f"Error handling tool call: {str(e)}")
        logger.error(traceback.format_exc())
        return {"tool_use_id": tool_use_id, "content": f"Error: {str(e)}"}


@cl.on_message
async def chat(message: cl.Message):
    """
    Main chat orchestration function.

    Responsible for:
    - Managing message history
    - Calling the LLM
    - Processing responses
    - Handling tool use
    - Sending UI messages
    - Updating session state
    """
    logger.info(f"Processing message in thread: {message.thread_id}")

    # Get current user and message history
    user: cl.PersistedUser = cl.user_session.get("user")
    messages = cl.user_session.get("messages")
    tools = cl.user_session.get("tools")

    # Add user message to history
    messages.append(
        {"role": "user", "content": [{"type": "text", "text": message.content}]}
    )

    # Call Claude
    response = call_claude(messages, tools)

    # Send assistant's text response to UI
    if response.content and response.content[0].type == "text":
        await cl.Message(content=response.content[0].text).send()

    # Update message history based on response type
    if response.stop_reason == "tool_use":
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
        tool_result = await handle_tool_call(user.id, response)

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
        follow_up_response = call_claude(messages, tools)

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


@cl.on_chat_resume
async def resume(thread: ThreadDict):
    cl.user_session.set("messages", thread["metadata"]["messages"])
