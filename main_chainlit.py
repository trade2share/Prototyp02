from typing import Optional, List, Tuple, Any
import asyncio
import chainlit as cl
from dotenv import load_dotenv, find_dotenv
from backend.core import run_llm

# Robustly load .env from project root
_dotenv_path = find_dotenv(usecwd=True)
if _dotenv_path:
    load_dotenv(_dotenv_path)


def _create_sources_string(sources: List[str]) -> str:
    if not sources:
        return ""
    lines = []
    for i, source in enumerate(sources, start=1):
        lines.append(f"\n{i}. {source}")
    return "".join(lines)


def _format_chat_history_for_backend(chat_history: List[Tuple[str, str]]) -> List[List[str]]:
    formatted: List[List[str]] = []
    for pair in chat_history:
        if len(pair) == 2:
            formatted.append([pair[0], pair[1]])
    return formatted


@cl.on_chat_start
async def start():
    if cl.user_session.get("user_prompt_history") is None:
        cl.user_session.set("user_prompt_history", [])
    if cl.user_session.get("chat_answer_history") is None:
        cl.user_session.set("chat_answer_history", [])

    user = cl.user_session.get("user")
    if user:
        await cl.Message(content=f"RAG Prototyp V.02\nFragen zum Thema relationale Datenbanken\n\nHallo {user.display_name or user.identifier}! Wie kann ich helfen?").send()
    else:
        await cl.Message(content="RAG Prototyp V.02\nFragen zum Thema relationale Datenbanken").send()

    # Render existing history (like Streamlit does at load)
    chat_answers = list(cl.user_session.get("chat_answer_history") or [])
    user_prompts = list(cl.user_session.get("user_prompt_history") or [])
    for answer, prompt in zip(chat_answers, user_prompts):
        await cl.Message(author="user", content=prompt).send()
        await cl.Message(author="assistant", content=answer).send()


@cl.on_message
async def on_message(message: cl.Message):
    user_prompts = list(cl.user_session.get("user_prompt_history") or [])
    chat_answers = list(cl.user_session.get("chat_answer_history") or [])

    # Build history as in Streamlit main.py
    chat_history_pairs: List[Tuple[str, str]] = list(zip(user_prompts, chat_answers))
    formatted_history = _format_chat_history_for_backend(chat_history_pairs)

    status_msg = cl.Message(content="Antwort wird generiert...")
    await status_msg.send()

    try:
        # Offload sync backend function to a thread to avoid blocking event loop
        loop = asyncio.get_running_loop()
        result: Any = await loop.run_in_executor(None, lambda: run_llm(query=message.content, chat_history=formatted_history))

        # Extract sources
        sources_set = set()
        if isinstance(result, dict) and "source" in result and result["source"]:
            for doc in result["source"]:
                if hasattr(doc, "metadata") and isinstance(doc.metadata, dict) and "source" in doc.metadata:
                    sources_set.add(doc.metadata["source"])

        formatted_response = f"{result.get('result', '')} \n\n Quelle: {_create_sources_string(list(sources_set))}"

        # Update history
        user_prompts.append(message.content)
        chat_answers.append(formatted_response)
        cl.user_session.set("user_prompt_history", user_prompts)
        cl.user_session.set("chat_answer_history", chat_answers)

        status_msg.content = formatted_response
        await status_msg.update()
    except Exception as e:
        status_msg.content = f"Ein Fehler ist aufgetreten: {str(e)}"
        await status_msg.update()


# Optional: validate/augment user from OAuth provider
@cl.oauth_callback
async def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict,
    default_user: cl.User,
    id_token: Optional[str] = None,
):
    identifier = (
        raw_user_data.get("sub")
        or raw_user_data.get("oid")
        or raw_user_data.get("id")
    )
    if not identifier:
        return None

    display_name = (
        raw_user_data.get("name")
        or raw_user_data.get("preferred_username")
        or raw_user_data.get("given_name")
    )
    email = raw_user_data.get("email") or raw_user_data.get("upn")

    user = cl.User(identifier=identifier, display_name=display_name, metadata={"email": email, "provider": provider_id})
    return user
