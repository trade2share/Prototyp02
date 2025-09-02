import os
from dotenv import load_dotenv

from langchain_community.document_loaders import AzureBlobStorageContainerLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pinecone import ServerlessSpec


def load_env():
    load_dotenv()
    return os.getenv("AZURE_STORAGE_CONNECTION_STRING"), os.getenv("AZURE_STORAGE_CONTAINER_NAME")


def load_documents():
    conn_str, container = load_env()
    if not conn_str or not container:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_CONTAINER_NAME must be set")
    
    docs = AzureBlobStorageContainerLoader(
        conn_str=conn_str, container=container)
    return docs.load()


def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    return chunks


 # change if desired



def chunk_embedding(chunks):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    if not api_key or not index_name:
        raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_NAME must be set")

    pc = Pinecone(api_key=api_key)
    index = pc.Index(name=index_name)

    vectorstore = PineconeVectorStore(index=index, embedding=embeddings)
    vectorstore.add_documents(chunks)
    





if __name__ == "__main__":
    docs = load_documents()
    chunks = split_documents(docs)
 
    print(f"Anzahl der Chunks: {len(chunks)}\n")
    chunk_embedding(chunks)


  




    