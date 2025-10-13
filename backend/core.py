from dotenv import load_dotenv
import os
from typing import Optional, List, Any, Sequence, Tuple

# LangChain-spezifische Imports
from langchain.chains.retrieval import create_retrieval_chain
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# Pinecone-Client
import pinecone

# Import aus deiner Hilfsdatei
# oder (innerhalb des Pakets)
from .utils import create_detailed_sources_string

# Umgebungsvariablen laden
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Diese Funktion formatiert die Chat-Historie für LangChain
def _format_history_for_langchain(chat_history: list = []) -> List[Any]:
    formatted_chat_history = []
    for message_pair in chat_history:
        if len(message_pair) == 2:
            formatted_chat_history.extend(
                [
                    ("human", message_pair[0]),
                    ("ai", message_pair[1])
                ]
            )
    return formatted_chat_history


# Asynchrone Hauptfunktion für die RAG-Kette mit Inline-Zitaten
async def run_llm_async(query: str, chat_history: list = [], callbacks: Optional[List[Any]] = None):
    # 1. Überprüfung der Umgebungsvariablen
    if not PINECONE_API_KEY or not PINECONE_INDEX_NAME:
        raise ValueError("PINECONE_API_KEY und PINECONE_INDEX_NAME müssen gesetzt sein.")

    # 2. Initialisierung der Clients und Modelle
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings)
    chat = ChatOpenAI(verbose=True, model="gpt-5-mini", temperature=1)

    # 3. Erstellung der Prompts und der RAG-Kette

    # Prompt, um die Eingabefrage basierend auf der Historie umzuformulieren
    rephrase_prompt = hub.pull("langchain-ai/chat-langchain-rephrase")
    history_aware_retriever = create_history_aware_retriever(
        llm=chat,
        retriever=vectorstore.as_retriever(),
        prompt=rephrase_prompt,
    )

    # System-Prompt, der das LLM anweist, Inline-Zitate zu erstellen
    QA_SYSTEM_PROMPT = """You are an assistant for question-answering tasks.
Your answer must be in German.
Use ONLY the following pieces of retrieved context to answer the question.
If the context isn't sufficient, just say that you don't know.

Crucial rule: For every single piece of information you use from the context, you MUST cite the source immediately after it using the format [source_N], where N is the number of the source document (e.g., source_1, source_2).
Do NOT write any sentence that uses context information without adding a citation to the end of that sentence.

Example:
Context:
source_1: LangChain ist ein Framework.
Answer: LangChain ist ein Framework [source_1].

Now, answer the user's question based on the following context:
<context>
{context}
</context>
"""
    
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", QA_SYSTEM_PROMPT),
            ("human", "{input}"),
        ]
    )
    
    # Die Retrieval- und Antwortschritte werden unten manuell verkettet,
    # damit wir die Kontext-Dokumente explizit als source_1, source_2, ... labeln können.
    
    # Formatierung der Historie für den Aufruf
    formatted_chat_history = _format_history_for_langchain(chat_history)

    # 4. Retrieval: Dokumente unter Berücksichtigung der Historie holen
    if callbacks:
        retrieved_docs = await history_aware_retriever.ainvoke(
            {"input": query, "chat_history": formatted_chat_history},
            config={"callbacks": callbacks},
        )
    else:
        retrieved_docs = await history_aware_retriever.ainvoke(
            {"input": query, "chat_history": formatted_chat_history}
        )

    # Kontext explizit nummerieren, damit das LLM zuverlässig [source_N] referenzieren kann
    context_parts: List[str] = []
    for idx, doc in enumerate(retrieved_docs, start=1):
        page_content = getattr(doc, "page_content", "") or ""
        context_parts.append(f"source_{idx}: {page_content}")
    enumerated_context = "\n\n".join(context_parts)

    # 5. Finales QA mit explizit nummeriertem Kontext ausführen
    if callbacks:
        llm_msg = await (qa_prompt | chat).ainvoke(
            {"input": query, "context": enumerated_context},
            config={"callbacks": callbacks},
        )
    else:
        llm_msg = await (qa_prompt | chat).ainvoke(
            {"input": query, "context": enumerated_context}
        )

    # Normalisiere Ausgabe
    answer_text = getattr(llm_msg, "content", None)
    if answer_text is None:
        answer_text = str(llm_msg)
        
    # 5. Nachbearbeitung der Ausgabe für die Anzeige im Frontend
    answer = answer_text
    context_docs = list(retrieved_docs or [])

    # Ersetze die [source_N]-Platzhalter im Text durch nummerierte, fettgedruckte Zitate
    for i, doc in enumerate(context_docs):
        answer = answer.replace(f"[source_{i+1}]", f" **[{i+1}]**")

    # Rufe deine Hilfsfunktion auf, um den detaillierten Quellen-String zu erstellen
    formatted_sources = create_detailed_sources_string(context_docs)

    # Kombiniere die Antwort mit der formatierten Quellenliste
    final_output = answer
    if formatted_sources:
        final_output += f"\n\n---\n**Quellen:**{formatted_sources}"

    # Gib ein sauberes Ergebnis-Dictionary zurück
    new_result = {
        "query": query,
        "result": final_output,
        "source_documents": context_docs # Behalte die originalen Dokumente für evtl. weitere Zwecke
    }

    return new_result

# Block für direktes Ausführen der Datei (optional für Tests)
if __name__ == "__main__":
    # Hier könntest du Testaufrufe einfügen, z.B. mit asyncio.run()
    # import asyncio
    # async def main():
    #     response = await run_llm_async(query="Was ist der Sinn von RAG?")
    #     print(response["result"])
    # asyncio.run(main())
    pass

