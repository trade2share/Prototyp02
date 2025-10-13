from typing import Optional, List, Tuple, Any
import asyncio
import hashlib
import chainlit as cl
from dotenv import load_dotenv, find_dotenv
from backend.core import run_llm_async
from langchain_core.callbacks import AsyncCallbackHandler

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


def _create_detailed_sources_string(docs: Optional[List[Any]]) -> str:
    """Return a formatted string with [Source, Seite, ChunkID] for each retrieved chunk.

    Falls 'chunk_id' oder 'page' nicht vorhanden sind, werden sie robust
    aus anderen Metadaten abgeleitet bzw. ein stabiler Hash erzeugt.
    """
    if not docs:
        return ""

    lines: List[str] = []
    seen_keys = set()

    for idx, doc in enumerate(docs, start=1):
        metadata = getattr(doc, "metadata", {}) or {}
        page_content = getattr(doc, "page_content", "") or ""

        source = (
            metadata.get("source")
            or metadata.get("file_path")
            or metadata.get("filepath")
            or "Unbekannt"
        )

        page = metadata.get("page_number")
        if page is None:
            page = metadata.get("page_number")
        if page is None:
            page = metadata.get("page_index")

        chunk_id = (
            metadata.get("chunk_id")
            or metadata.get("id")
            or metadata.get("doc_id")
        )

        if not chunk_id:
            # Erzeuge stabilen, kurzen Hash basierend auf Quelle, Seite und Content-Auszug
            hash_input = f"{source}|{page}|{page_content[:80]}".encode("utf-8", "ignore")
            chunk_id = hashlib.sha1(hash_input).hexdigest()[:8]

        key = (str(source), str(page), str(chunk_id))
        if key in seen_keys:
            continue
        seen_keys.add(key)

        line = f"\n{idx}. {source}"
        if page is not None:
            line += f", Seite: {page}"
        line += f", ChunkID: {chunk_id}"

        lines.append(line)

    return "".join(lines)


def _format_chat_history_for_backend(chat_history: List[Tuple[str, str]]) -> List[List[str]]:
    formatted: List[List[str]] = []
    for pair in chat_history:
        if len(pair) == 2:
            formatted.append([pair[0], pair[1]])
    return formatted


class UIProgressHandler(AsyncCallbackHandler):
    def __init__(self, status_msg: cl.Message) -> None:
        self.status_msg = status_msg
        self.llm_call_count = 0

    async def _set(self, text: str) -> None:
        self.status_msg.content = text
        await self.status_msg.update()

    async def on_llm_start(self, serialized, prompts, **kwargs) -> None:
        # First LLM: rephrase/history aware query; second LLM: final answer
        self.llm_call_count += 1
        if self.llm_call_count == 1:
            await self._set("Rephrase / Kontext aufbereiten…")
        else:
            await self._set("Antwort wird erstellt…")

    async def on_retriever_start(self, serialized, query, **kwargs) -> None:
        await self._set("Dokumente werden gesucht (Retrieval)…")

    async def on_retriever_end(self, documents, **kwargs) -> None:
        await self._set("Dokumente kombiniert…")

    async def on_chain_start(self, serialized, inputs, **kwargs) -> None:
        # Heuristik: combine/stuff chain erkannt -> kombinierte Dokumente
        try:
            name = (serialized.get("id", {}) or {}).get("name") or serialized.get("name") or ""
        except Exception:
            name = ""
        if isinstance(name, str) and ("combine" in name.lower() or "stuff" in name.lower()):
            await self._set("Dokumente kombiniert…")


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
        # Animated steps + custom phase labels
        lc_cb = cl.LangchainCallbackHandler(stream_final_answer=True)
        ui_cb = UIProgressHandler(status_msg)

        result: Any = await run_llm_async(
            query=message.content,
            chat_history=formatted_history,
            callbacks=[lc_cb, ui_cb],
        )

        # Verwende die vom Backend bereits formatierte Antwort inkl. Quellen
        formatted_response = result.get("result", "") if isinstance(result, dict) else str(result)

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
