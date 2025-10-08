from __future__ import annotations

from typing import Any, Iterable, List, Sequence, Tuple
import hashlib


def create_sources_string(sources: Iterable[str] | None) -> str:
    if not sources:
        return ""
    lines: List[str] = []
    for i, source in enumerate(list(sources), start=1):
        lines.append(f"\n{i}. {source}")
    return "".join(lines)


def create_detailed_sources_string(docs: Sequence[Any] | None) -> str:
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


def format_chat_history_for_backend(chat_history: Sequence[Tuple[str, str]]) -> List[List[str]]:
    formatted: List[List[str]] = []
    for pair in chat_history:
        if len(pair) == 2:
            formatted.append([pair[0], pair[1]])
    return formatted


