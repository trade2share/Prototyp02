from backend.core import run_llm
import streamlit as st
import hashlib

st.title("RAG Prototyp V.02")
st.header("Fragen zum Thema relationale Datenbanken")

prompt = st.chat_input("Frage hier eingeben")

def create_sources_string(sources):
    if not sources:
        return ""
    
    sources_list = list(sources)
    sources_string = ""
    
    for i, source in enumerate(sources_list):
        sources_string += f"\n{i+1}. {source}"
    
    return sources_string


def create_detailed_sources_string(docs):
    """Return a formatted string with [Source, Seite, ChunkID] for each retrieved chunk.

    Falls 'chunk_id' oder 'page' nicht vorhanden sind, werden sie robust
    aus anderen Metadaten abgeleitet bzw. ein stabiler Hash erzeugt.
    """
    if not docs:
        return ""

    lines = []
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


# Initialize session state variables
if "user_prompt_history" not in st.session_state:
    st.session_state["user_prompt_history"] = []
if "chat_answer_history" not in st.session_state:
    st.session_state["chat_answer_history"] = []

# Display chat history first
if st.session_state["chat_answer_history"]:
    for i, (answer, user_prompt) in enumerate(zip(st.session_state["chat_answer_history"], st.session_state["user_prompt_history"])):
        st.chat_message("user").write(user_prompt)
        st.chat_message("assistant").write(answer)

# Handle new prompt
if prompt:
    # Add user message to chat
    st.chat_message("user").write(prompt)
    
    # Show loading message in chat
    with st.chat_message("assistant"):
        with st.spinner("Antwort wird generiert..."):
            try:
                # Create proper chat history format for LangChain
                chat_history = []
                for i, (answer, user_prompt) in enumerate(zip(st.session_state["chat_answer_history"], st.session_state["user_prompt_history"])):
                    chat_history.append([user_prompt, answer])
                
                generated_answer = run_llm(query=prompt, chat_history=chat_history)
                
                # Extract detailed sources: [Source, Seite, ChunkID] for all chunks
                detailed_sources = create_detailed_sources_string(generated_answer.get("source"))
                formatted_response = f"""{generated_answer["result"]} \n\n Quellen (Dokument/Seite/Chunk): {detailed_sources}"""
                
                # Display the response
                st.write(formatted_response)
                
                # Add to history
                st.session_state["user_prompt_history"].append(prompt)
                st.session_state["chat_answer_history"].append(formatted_response)
                
                
            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {str(e)}")
