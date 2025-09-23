from backend.core import run_llm
import streamlit as st

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
                
                # Extract sources from the context documents
                sources = set()
                if "source" in generated_answer and generated_answer["source"]:
                    for doc in generated_answer["source"]:
                        if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                            sources.add(doc.metadata["source"])
                
                formatted_response = f"""{generated_answer["result"]} \n\n Quelle: {create_sources_string(sources)}"""
                
                # Display the response
                st.write(formatted_response)
                
                # Add to history
                st.session_state["user_prompt_history"].append(prompt)
                st.session_state["chat_answer_history"].append(formatted_response)
                
                
            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {str(e)}")
