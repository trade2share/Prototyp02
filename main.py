from backend.core import run_llm
import streamlit as st

st.title("RAG Prototyp V.02")
st.header("Frage zum Thema Datenbanken")

prompt = st.chat_input("Frage hier eingeben")

def create_sources_string(sources):
    if not sources:
        return ""
    
    sources_list = list(sources)
    sources_string = ""
    
    for i, source in enumerate(sources_list):
        sources_string += f"\n{i+1}. {source}"
    
    return sources_string


if prompt:
    with st.spinner("Antwort wird generiert..."):
        try:
            generated_answer = run_llm(query=prompt)
            
            # Extract sources from the context documents
            sources = set()
            if "source" in generated_answer and generated_answer["source"]:
                for doc in generated_answer["source"]:
                    if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                        sources.add(doc.metadata["source"])
            
            formatted_response = f"""{generated_answer["result"]} \n\n Quelle: {create_sources_string(sources)}"""
            
            st.write(formatted_response)
            
        except Exception as e:
            st.error(f"Fehler beim Generieren der Antwort: {str(e)}")
            st.write("Debug - Full error:", e)

