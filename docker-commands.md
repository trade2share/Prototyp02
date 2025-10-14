# Docker Commands (Chainlit) für Azure Container Registry

## 1. Docker Image bauen
```bash
docker build -t rag-prototyp:latest .
```

## 2. Image für Azure Container Registry taggen
```bash
# Ersetzen Sie "your-registry-name" mit dem Namen Ihrer Registry
docker tag rag-prototyp:latest your-registry-name.azurecr.io/rag-prototyp:latest
```

## 3. Bei Azure Container Registry anmelden
```bash
az acr login --name your-registry-name
```

## 4. Image zu Azure Container Registry pushen
```bash
docker push your-registry-name.azurecr.io/rag-prototyp:latest
```

## 5. Container lokal testen
```bash
docker run -p 8000:8000 --env-file .env rag-prototyp:latest
```

## 6. Container in Azure Container Instances deployen
```bash
az container create \
  --resource-group your-resource-group \
  --name rag-prototyp \
  --image your-registry-name.azurecr.io/rag-prototyp:latest \
  --ports 8000 \
  --dns-name-label your-dns-label \
  --environment-variables \
    AZURE_OPENAI_API_KEY="your-azure-openai-key" \
    AZURE_OPENAI_ENDPOINT="your-azure-openai-endpoint" \
    AZURE_OPENAI_API_VERSION="2024-02-01" \
    AZURE_AI_SEARCH_SERVICE_NAME="your-search-service-name" \
    AZURE_AI_SEARCH_INDEX_NAME="your-index-name" \
    AZURE_AI_SEARCH_API_KEY="your-search-api-key" \
    AZURE_STORAGE_CONNECTION_STRING="your-storage-connection-string" \
    AZURE_STORAGE_CONTAINER_NAME="your-container-name"
```

## Wichtige Hinweise:
- Ersetzen Sie alle Platzhalter (your-*) mit Ihren tatsächlichen Werten
- Stellen Sie sicher, dass Sie bei Azure angemeldet sind (`az login`)
- Die Umgebungsvariablen müssen beim Deployment gesetzt werden
- Der Container läuft auf Port 8000 (Chainlit)
