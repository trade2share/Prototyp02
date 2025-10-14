import os
import time
import re
import unicodedata
from dotenv import load_dotenv
from pydantic import SecretStr
from typing import cast

from langchain_community.document_loaders import AzureBlobStorageContainerLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.documents import Document
from openai import RateLimitError
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential


def sanitize_document_key(value: str) -> str:
    """Sanitizes a string to a valid Azure Search document key.
    Allowed: letters, digits, underscore (_), dash (-), equal sign (=).
    """
    if value is None:
        value = ""
    # Remove accents/diacritics and normalize
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    # Replace any disallowed char with underscore
    sanitized = re.sub(r"[^A-Za-z0-9_\-=]", "_", normalized)
    # Collapse multiple underscores and trim
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    # Ensure non-empty
    if not sanitized:
        sanitized = "doc"
    return sanitized


def load_env():
    load_dotenv()
    return os.getenv("AZURE_STORAGE_CONNECTION_STRING"), os.getenv("AZURE_STORAGE_CONTAINER_NAME")


def load_azure_openai() -> tuple[str, str, str | None, str]:
    """Lädt Azure OpenAI Umgebungsvariablen."""
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    deployment_name = "text-embedding-3-small"
    
    if not all([api_key, azure_endpoint, deployment_name]):
        raise ValueError("AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT und Deployment-Name müssen gesetzt sein")
    
    api_key = cast(str, api_key)
    azure_endpoint = cast(str, azure_endpoint)
    return api_key, azure_endpoint, api_version, deployment_name


def load_azure_ai_search_env() -> tuple[str, str, str]:
    """Lädt Azure AI Search Umgebungsvariablen."""
    service_name = os.getenv("AZURE_AI_SEARCH_SERVICE_NAME")
    index_name = os.getenv("AZURE_AI_SEARCH_INDEX_NAME")
    api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")

    if not service_name or not index_name or not api_key:
        raise ValueError(
            "AZURE_AI_SEARCH_SERVICE_NAME, AZURE_AI_SEARCH_INDEX_NAME und AZURE_AI_SEARCH_API_KEY müssen gesetzt sein"
        )
    return service_name, index_name, api_key


def load_documents():
    conn_str, container = load_env()
    if not conn_str or not container:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_CONTAINER_NAME must be set")
    
    print("Lade Dokumente aus Azure Blob Storage...")
    docs = AzureBlobStorageContainerLoader(
        conn_str=conn_str, container=container)
    documents = docs.load()
    print(f"✅ {len(documents)} Dokumente geladen")
    return documents


def split_documents(docs):
    """Teilt Dokumente in Chunks und reichert die Metadaten an."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    
    print(f"Dokumente in {len(chunks)} Chunks aufgeteilt. Beginne Anreicherung...")
    
    for i, chunk in enumerate(chunks):
        source = chunk.metadata.get('source', 'Unbekannte Quelle')
        page_num = chunk.metadata.get('page', 0)
        
        chunk.metadata['source_filename'] = os.path.basename(source)
        chunk.metadata['page_number'] = page_num + 1 if isinstance(page_num, int) else page_num
        raw_chunk_id = f"{chunk.metadata['source_filename']}_seite-{chunk.metadata['page_number']}_chunk-{i}"
        chunk_id = sanitize_document_key(raw_chunk_id)
        chunk.metadata['chunk_id'] = chunk_id
        chunk.metadata['id'] = chunk_id
    
    print("✅ Anreicherung der Metadaten abgeschlossen")
    return chunks


def chunk_embedding(chunks, batch_size=16, delay_between_batches=2):
    """
    Erstellt Embeddings und speichert sie direkt in Azure AI Search.
    Verwendet das 'embedding' Feld (nicht 'content_vector').
    """
    service_name, index_name, search_api_key = load_azure_ai_search_env()
    openai_api_key, openai_endpoint, openai_api_version, openai_deployment = load_azure_openai()
    
    endpoint = f"https://{service_name}.search.windows.net"
    
    # Azure OpenAI Embeddings
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=openai_deployment,
        azure_endpoint=openai_endpoint,
        api_key=SecretStr(openai_api_key),
        api_version=openai_api_version,
    )

    # Direkter Azure Search Client (nicht LangChain VectorStore!)
    search_client = SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(search_api_key),
    )
    
    total_chunks = len(chunks)
    processed_chunks = 0
    
    print(f"\n🚀 Starte Stapelverarbeitung von {total_chunks} Chunks...")
    
    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"  📦 Verarbeite Batch {batch_num} ({len(batch)} Chunks)...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Embeddings für alle Texte im Batch berechnen
                texts = [doc.page_content for doc in batch]
                vectors = embeddings.embed_documents(texts)

                # Dokumente für den Index vorbereiten (mit 'embedding' Feld!)
                docs_to_upload = []
                for doc, vec in zip(batch, vectors):
                    meta = doc.metadata or {}
                    doc_id = meta.get('id') or meta.get('chunk_id')
                    if not doc_id:
                        # Fallback: deterministische ID
                        source_fn = meta.get('source_filename') or meta.get('source') or 'unknown'
                        page_no = meta.get('page_number', 0)
                        doc_id = f"{source_fn}_seite-{page_no}_auto"
                    doc_id = sanitize_document_key(str(doc_id))
                    
                    docs_to_upload.append({
                        'id': doc_id,
                        'content': doc.page_content,
                        'embedding': vec,  # WICHTIG: 'embedding' nicht 'content_vector'!
                        'source': meta.get('source_filename') or meta.get('source') or '',
                        'page_number': int(meta.get('page_number', 0)),
                        'chunk_id': meta.get('chunk_id') or doc_id,
                    })

                # Upload zu Azure AI Search
                results = search_client.upload_documents(documents=docs_to_upload)
                failed = [r for r in results if not r.succeeded]
                if failed:
                    raise Exception(f"{len(failed)} Dokument(e) fehlgeschlagen: {failed[0].error_message}")

                processed_chunks += len(batch)
                print(f"  ✅ Batch {batch_num} erfolgreich ({processed_chunks}/{total_chunks} gesamt)")
                break
                
            except RateLimitError:
                wait_time = 60 * (attempt + 1)
                print(f"  ⏳ Rate-Limit erreicht! Warte {wait_time}s (Versuch {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            except Exception as e:
                print(f"  ❌ Fehler in Batch {batch_num}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    print(f"  ❌ FEHLER: Batch {batch_num} nach {max_retries} Versuchen fehlgeschlagen")
                    break
        
        if i + batch_size < total_chunks:
            time.sleep(delay_between_batches)
    
    print(f"\n🎉 Stapelverarbeitung abgeschlossen! {processed_chunks}/{total_chunks} Chunks verarbeitet")
    return processed_chunks
    





if __name__ == "__main__":
    docs = load_documents()
    chunks = split_documents(docs)
 
    print(f"Anzahl der Chunks: {len(chunks)}\n")
    chunk_embedding(chunks)


  




    