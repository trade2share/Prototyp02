from dotenv import load_dotenv
import os
from typing import Optional, List, Any
from langchain.chains.retrieval import create_retrieval_chain
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import create_history_aware_retriever
from utils import create_detailed_sources_string
import pinecone


load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

def _format_history_for_langchain(chat_history: list = []) -> List[Any]:
    formatted_chat_history = []
    for message_pair in chat_history:
        if len(message_pair) == 2:
            formatted_chat_history.extend([
                ("human", message_pair[0]),
                ("ai", message_pair[1])
            ])
    return formatted_chat_history


def run_llm(query: str, chat_history: list = [], callbacks: Optional[List[Any]] = None): # with Chat history
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

    rephase_prompt = hub.pull("langchain-ai/chat-langchain-rephrase")
    history_aware_retriever = create_history_aware_retriever(llm=chat, retriever=vectorstore.as_retriever(), prompt=rephase_prompt) #Adding history aware retriever 

    qa = create_retrieval_chain(retriever=history_aware_retriever, combine_docs_chain=stuff_documents_chain) #RAG Chain
    
    # Prepare chat history in the format expected by LangChain
    formatted_chat_history = _format_history_for_langchain(chat_history)

    # Allow Chainlit to hook into LangChain steps via callbacks (sync path)
    if callbacks:
        result = qa.invoke(
            input={"input": query, "chat_history": formatted_chat_history},
            config={"callbacks": callbacks},
        )
    else:
        result = qa.invoke(input={"input": query, "chat_history": formatted_chat_history})

    new_result = {"query": result["input"], "result": result["answer"], "source": result["context"]}

    return new_result 


async def run_llm_async(query: str, chat_history: list = [], callbacks: Optional[List[Any]] = None):
    # Check if environment variables are set
    if not PINECONE_API_KEY or not PINECONE_INDEX_NAME:
        raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_NAME must be set in environment variables")

    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings)
    chat  = ChatOpenAI(verbose=True, model="gpt-4o-mini", temperature=0)

    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    stuff_documents_chain = create_stuff_documents_chain(chat, retrieval_qa_chat_prompt)

    rephase_prompt = hub.pull("langchain-ai/chat-langchain-rephrase")
    history_aware_retriever = create_history_aware_retriever(
        llm=chat,
        retriever=vectorstore.as_retriever(),
        prompt=rephase_prompt,
    )

    qa = create_retrieval_chain(
        retriever=history_aware_retriever,
        combine_docs_chain=stuff_documents_chain,
    )

    formatted_chat_history = _format_history_for_langchain(chat_history)

    if callbacks:
        result = await qa.ainvoke(
            input={"input": query, "chat_history": formatted_chat_history},
            config={"callbacks": callbacks},
        )
    else:
        result = await qa.ainvoke(
            input={"input": query, "chat_history": formatted_chat_history}
        )

    new_result = {"query": result["input"], "result": result["answer"], "source": result["context"]}
    return new_result

if __name__ == "__main__":
    pass





