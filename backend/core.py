from dotenv import load_dotenv
import os
from langchain.chains.retrieval import create_retrieval_chain
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import pinecone


load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

def run_llm(query: str):
    # Check if environment variables are set
    if not PINECONE_API_KEY or not PINECONE_INDEX_NAME:
        raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_NAME must be set in environment variables")
    
    # Initialize Pinecone client
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
    
    # Get the index
    index = pc.Index(PINECONE_INDEX_NAME)
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings)  #retriever
    chat  = ChatOpenAI(verbose=True, model="gpt-4o-mini", temperature=0)

    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    stuff_documents_chain = create_stuff_documents_chain(chat, retrieval_qa_chat_prompt) #augmentation

    qa = create_retrieval_chain(retriever=vectorstore.as_retriever(), combine_docs_chain=stuff_documents_chain) #RAG Chain
    result = qa.invoke({"input": query})

    new_result = {"query": result["input"], "result": result["answer"], "source": result["context"]}

    return new_result 

if __name__ == "__main__":
    query = "Welche Recovery Möglichkeiten hat eine relationale Datenbank?"
    result = run_llm(query)
    print(result["answer"])   

    





