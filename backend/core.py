from dotenv import load_dotenv
import os
from typing import Optional, List, Any, Sequence, Tuple
from pydantic import SecretStr

# LangChain-spezifische Imports
from langchain.chains.retrieval import create_retrieval_chain
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun, AsyncCallbackManagerForRetrieverRun
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

# Azure Search SDK
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

# Import aus deiner Hilfsdatei
from .utils import create_detailed_sources_string

# Umgebungsvariablen laden
load_dotenv()

# Azure Configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")  # Für Embeddings
AZURE_OPENAI_CHAT_API_VERSION = os.getenv("AZURE_OPENAI_CHAT_API_VERSION", "2024-12-01-preview")  # Für o4-mini

AZURE_AI_SEARCH_SERVICE_NAME = os.getenv("AZURE_AI_SEARCH_SERVICE_NAME")
AZURE_AI_SEARCH_INDEX_NAME = os.getenv("AZURE_AI_SEARCH_INDEX_NAME")
AZURE_AI_SEARCH_API_KEY = os.getenv("AZURE_AI_SEARCH_API_KEY")

# Custom Retriever für Azure AI Search mit 'embedding' Feld
class AzureSearchRetriever(BaseRetriever):
    """Custom Retriever für Azure AI Search, der das 'embedding' Feld verwendet."""
    
    search_client: Any
    embeddings: AzureOpenAIEmbeddings
    k: int = 4  # Anzahl der zu retrievenden Dokumente
    
    class Config:
        arbitrary_types_allowed = True
    
    def _get_relevant_documents(
        self, query: str, *, run_manager: Optional[CallbackManagerForRetrieverRun] = None
    ) -> List[Document]:
        """Synchrone Methode - ruft die async Version auf."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._aget_relevant_documents(query))
    
    async def _aget_relevant_documents(
        self, query: str, *, run_manager: Optional[AsyncCallbackManagerForRetrieverRun] = None
    ) -> List[Document]:
        """Asynchrone Methode für Azure AI Search Retrieval mit 'embedding' Feld."""
        # 1. Query Embedding erstellen
        query_vector = await self.embeddings.aembed_query(query)
        
        # 2. Vector Query für Azure Search erstellen
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=self.k,
            fields="embedding"  # WICHTIG: Verwendet 'embedding' statt 'content_vector'
        )
        
        # 3. Azure Search abfragen
        results = self.search_client.search(
            search_text=None,  # Nur Vektor-Suche, keine Keyword-Suche
            vector_queries=[vector_query],
            select=["id", "content", "source", "page_number", "chunk_id"],
            top=self.k
        )
        
        # 4. Ergebnisse in LangChain Documents konvertieren
        documents = []
        for result in results:
            doc = Document(
                page_content=result.get("content", ""),
                metadata={
                    "id": result.get("id", ""),
                    "source": result.get("source", ""),
                    "page_number": result.get("page_number"),
                    "chunk_id": result.get("chunk_id", ""),
                    "score": result.get("@search.score", 0.0)
                }
            )
            documents.append(doc)
        
        return documents


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
    if not AZURE_AI_SEARCH_SERVICE_NAME or not AZURE_AI_SEARCH_INDEX_NAME or not AZURE_AI_SEARCH_API_KEY:
        raise ValueError("Azure AI Search Umgebungsvariablen müssen gesetzt sein.")
    
    if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
        raise ValueError("Azure OpenAI Umgebungsvariablen müssen gesetzt sein.")

    # 2. Initialisierung der Clients und Modelle
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding-3-small",
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=SecretStr(AZURE_OPENAI_API_KEY) if AZURE_OPENAI_API_KEY else None
    )
    
    # Azure Search Client (direkt, nicht über LangChain VectorStore!)
    endpoint = f"https://{AZURE_AI_SEARCH_SERVICE_NAME}.search.windows.net"
    search_client = SearchClient(
        endpoint=endpoint,
        index_name=AZURE_AI_SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(AZURE_AI_SEARCH_API_KEY)
    )
    
    # Custom Retriever, der das 'embedding' Feld verwendet
    retriever = AzureSearchRetriever(
        search_client=search_client,
        embeddings=embeddings,
        k=4  # Anzahl der zu retrievenden Dokumente
    )
    
    chat = AzureChatOpenAI(
        api_version=AZURE_OPENAI_CHAT_API_VERSION,  # ✅ Separate API Version für o4-mini
        azure_deployment="o4-mini",
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=SecretStr(AZURE_OPENAI_API_KEY) if AZURE_OPENAI_API_KEY else None,
        temperature=1,  # ✅ Niedriger für konsistentere, faktenbasierte Antworten
        verbose=True
    )

    # 3. Erstellung der Prompts und der RAG-Kette

    # Prompt, um die Eingabefrage basierend auf der Historie umzuformulieren
    rephrase_prompt = hub.pull("langchain-ai/chat-langchain-rephrase")
    history_aware_retriever = create_history_aware_retriever(
        llm=chat,
        retriever=retriever,  # Verwendet unseren Custom Retriever
        prompt=rephrase_prompt,
    )

    # System-Prompt optimiert für o4-mini - weniger streng, klarer
    QA_SYSTEM_PROMPT = """Du bist ein hilfreicher Assistent für Fragen zu relationalen Datenbanken.

Deine Aufgabe:
Beantworte die Frage des Nutzers auf Deutsch
Nutze die unten bereitgestellten Kontextinformationen
Zitiere jede verwendete Information mit [source_N] am Ende des Satzes
Wenn die Kontextinformationen relevant sind, nutze sie für deine Antwort
Wenn du unsicher bist, gib trotzdem eine hilfreiche Antwort basierend auf dem Kontext

Wichtig: Nutze den bereitgestellten Kontext aktiv! Die Informationen sind relevant für die Frage.

Kontext:
{context}

Antworte jetzt auf die Frage des Nutzers."""
    
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
        metadata = getattr(doc, "metadata", {})
        source = metadata.get("source", "Unbekannt")
        page = metadata.get("page_number", "?")
        
        # Debug-Ausgabe für besseres Verständnis
        print(f"📄 Retrieved Doc {idx}: {source}, Seite {page}, Length: {len(page_content)}")
        print(f"   Preview: {page_content[:100]}...")
        
        context_parts.append(f"source_{idx}: {page_content}")
    enumerated_context = "\n\n".join(context_parts)
    
    print(f"\n✅ Total Context Length: {len(enumerated_context)} Zeichen")
    print(f"✅ Anzahl Dokumente: {len(retrieved_docs)}")

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

