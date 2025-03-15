from typing import Dict, Optional

import anthropic
import chainlit as cl
from chainlit.logger import logger
from composio_claude import Action, App, ComposioToolSet
from dotenv import load_dotenv
import os

load_dotenv()

anthropic_client = anthropic.AsyncAnthropic()
toolset = ComposioToolSet()


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
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
                "redirect_uri": "https://stunning-cheerful-adder.ngrok-free.app/"
            }
        )
        return integration_obj
    else:
        return integrations[0]


@cl.action_callback("GitHub")
async def connect_github(action: cl.Action):
    app_name = action.payload.get("value")
    app_enum = getattr(App, app_name)
    user: cl.PersistedUser = cl.user_session.get("user")
    integration = create_integration_if_not_exists(app_enum)
    entity = toolset.get_entity(user.id)

    conn_req = entity.initiate_connection(
        app_name,
        auth_mode="OAUTH2",
        integration=integration,
        use_composio_auth=False
    )
    await cl.Message(content=f"Click here to connect: {conn_req.redirectUrl}")
    # Optionally remove the action button from the chatbot user interface
    await action.remove()


@cl.on_chat_start
async def start_chat():
    actions = [
        cl.Action(name="GitHub", payload={"value": "github"}, label="GitHub 💻"),
        cl.Action(name="Gmail", payload={"value": "gmail"}, label="Gmail 📧"),
    ]
    await cl.Message(
        content="Interact with this action button:", actions=actions
    ).send()
    cl.user_session.set("messages", [])


@cl.step(type="tool")
async def tool():
    pass


async def call_claude(query: str):
    messages = cl.user_session.get("messages")
    messages.append({"role": "user", "content": query})

    msg = cl.Message(content="", author="Claude")

    stream = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=messages,
        max_tokens=1000,
        stream=True,
    )

    async for data in stream:
        if data.type == "content_block_delta":
            await msg.stream_token(data.delta.text)

    await msg.send()
    messages.append({"role": "assistant", "content": msg.content})
    cl.user_session.set("messages", messages)


@cl.on_message
async def chat(message: cl.Message):
    await call_claude(message.content)
