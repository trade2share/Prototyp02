# RAG Prototyp V.02 - Streamlit vs Chainlit Vergleich

Dieses Projekt demonstriert dieselbe RAG (Retrieval-Augmented Generation) Funktionalität mit zwei verschiedenen Web-Frameworks: **Streamlit** und **Chainlit**.

## 🚀 Schnellstart

### Streamlit App starten:
```bash
./start_streamlit.sh
# oder
streamlit run main.py --server.port 8501
```
**URL:** http://localhost:8501

### Chainlit App starten:
```bash
./start_chainlit.sh
# oder
chainlit run main_chainlit.py --port 8000
```
**URL:** http://localhost:8000

## 📁 Projektstruktur

```
├── main.py                 # Streamlit RAG App
├── main_chainlit.py        # Chainlit RAG App
├── start_streamlit.sh      # Streamlit Start-Skript
├── start_chainlit.sh       # Chainlit Start-Skript
├── backend/
│   └── core.py            # Gemeinsame RAG-Logik
├── ingestion.py           # Dokumentenverarbeitung
└── requirements.txt       # Dependencies (beide Frameworks)
```

## 🔄 Gemeinsame Funktionalität

Beide Apps bieten:
- **RAG-System** mit LangChain und Pinecone
- **Chat-History** für kontextuelle Gespräche
- **Quellen-Anzeige** aus den geladenen Dokumenten
- **Azure Blob Storage** Integration
- **OpenAI GPT-4o-mini** als LLM
- **Thema:** Fragen zu relationalen Datenbanken

## ⚡ Framework-Unterschiede

### Streamlit (`main.py`)
**Vorteile:**
- ✅ Einfache, deklarative Syntax
- ✅ Schnelle Prototypen-Entwicklung
- ✅ Integrierte Widgets (sliders, buttons, etc.)
- ✅ Automatische Session-State-Verwaltung
- ✅ Große Community und Dokumentation

**Nachteile:**
- ❌ Weniger flexibel für komplexe Chat-Interfaces
- ❌ Begrenzte Customization-Möglichkeiten
- ❌ Weniger "natürliche" Chat-Erfahrung

**Code-Beispiel:**
```python
st.title("RAG Prototyp V.02")
prompt = st.chat_input("Frage hier eingeben")
st.chat_message("user").write(prompt)
```

### Chainlit (`main_chainlit.py`)
**Vorteile:**
- ✅ Speziell für Chat-Apps entwickelt
- ✅ Natürliche Chat-Interface-Erfahrung
- ✅ Eingebaute Message-Handling
- ✅ Async/await Support
- ✅ Bessere Chat-UI-Komponenten
- ✅ Starter-Nachrichten für bessere UX

**Nachteile:**
- ❌ Jüngeres Framework (weniger Community)
- ❌ Weniger Widgets außerhalb von Chat
- ❌ Begrenzte Customization für andere UI-Elemente

**Code-Beispiel:**
```python
@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()
    # ... processing ...
    await msg.update()
```

## 🎯 UI/UX Unterschiede

### Streamlit
- **Layout:** Traditionelle Web-App mit Widgets
- **Chat:** Chat-Input am unteren Rand, History oben
- **Styling:** Standard Streamlit-Theme
- **Interaktion:** Input-Feld + Enter/Send-Button

### Chainlit
- **Layout:** Chat-First Design (wie WhatsApp/Discord)
- **Chat:** Vollbild-Chat-Interface
- **Styling:** Moderne Chat-UI mit besserer Typografie
- **Interaktion:** Natürliche Chat-Erfahrung mit Typing-Indikatoren

## 🔧 Technische Unterschiede

| Feature | Streamlit | Chainlit |
|---------|-----------|----------|
| **Architektur** | Synchron | Asynchron |
| **Session Management** | `st.session_state` | `cl.user_session` |
| **Message Handling** | Manuell | Eingebaut |
| **UI Components** | Viele Widgets | Chat-fokussiert |
| **Customization** | CSS/HTML möglich | Begrenzt |
| **Performance** | Gut | Besser für Chat |

## 🛠️ Entwicklung

### Neue Features hinzufügen:

1. **Backend-Logik** in `backend/core.py` ändern
2. **Streamlit-Interface** in `main.py` anpassen
3. **Chainlit-Interface** in `main_chainlit.py` anpassen

### Dependencies installieren:
```bash
pip install -r requirements.txt
```

## 🎨 Customization

### Streamlit Theme anpassen:
Erstelle `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
```

### Chainlit Theme anpassen:
Erstelle `chainlit.md`:
```markdown
# Welcome to RAG Chat
Your custom welcome message here.
```

## 📊 Performance-Vergleich

Beide Apps nutzen dieselbe Backend-Logik, daher ist die **RAG-Performance identisch**. Unterschiede liegen in:

- **UI-Responsiveness:** Chainlit fühlt sich flüssiger an
- **Memory-Usage:** Streamlit etwas höher durch mehr UI-Komponenten
- **Startup-Time:** Beide ähnlich schnell

## 🚀 Deployment

Beide Apps können auf dieselbe Weise deployed werden:
- **Azure Container Instances** (siehe `azure-deployment.yml`)
- **Docker** (siehe `Dockerfile`)
- **Streamlit Cloud** (für Streamlit)
- **Chainlit Cloud** (für Chainlit)

## 💡 Empfehlungen

**Streamlit verwenden wenn:**
- Du schnell prototypen möchtest
- Du viele verschiedene UI-Widgets brauchst
- Du ein traditionelles Web-App-Layout bevorzugst

**Chainlit verwenden wenn:**
- Chat-Interface im Fokus steht
- Du eine moderne Chat-Erfahrung willst
- Du asynchrone Verarbeitung nutzen möchtest

## 🔍 Nächste Schritte

1. **Beide Apps testen** und Unterschiede erleben
2. **Eigene Features** hinzufügen (z.B. File-Upload)
3. **Performance messen** mit eigenen Daten
4. **UI/UX** nach eigenen Präferenzen anpassen

---

**Happy Coding! 🎉**

Beide Frameworks haben ihre Stärken - wähle das, was am besten zu deinem Use Case passt!
