# Azure RAG System Deployment Guide

## Übersicht

Dieser Guide beschreibt, wie Sie das RAG-System auf Azure deployen und für die Cloud skalieren. Das System nutzt Azure Container Apps für die Skalierung und Azure Blob Storage für die Dokumentenverwaltung.

## 🏗️ Architektur

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Browser  │───▶│  Azure Container │───▶│  Azure AI       │
│                 │    │  Apps (Scalable) │    │  Search         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Azure Blob       │
                       │ Storage          │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Azure OpenAI     │
                       │                  │
                       └──────────────────┘
```

## 📋 Voraussetzungen

- Azure CLI installiert und konfiguriert
- Azure Subscription mit ausreichenden Berechtigungen
- Docker installiert
- Python 3.11+
- Azure OpenAI Service eingerichtet
- Azure AI Search Service eingerichtet
- Azure Blob Storage Account eingerichtet

## 🚀 Schnellstart

### 1. Umgebungsvariablen konfigurieren

```bash
# Kopieren Sie die Vorlage
cp azure-env-template.env .env

# Bearbeiten Sie die .env-Datei mit Ihren Werten
nano .env
```

### 2. Azure Login

```bash
az login
az account set --subscription "Ihre-Subscription-ID"
```

### 3. Deployment ausführen

```bash
# Skript ausführbar machen
chmod +x azure-deploy.sh

# Deployment starten
./azure-deploy.sh
```

## 🔧 Manuelle Deployment-Schritte

### 1. Resource Group erstellen

```bash
az group create --name rag-system-rg --location westeurope
```

### 2. Azure Container Registry

```bash
az acr create --resource-group rag-system-rg --name ragsystemacr --sku Basic --admin-enabled true
az acr login --name ragsystemacr
```

### 3. Docker Image bauen und pushen

```bash
# Image bauen
docker build -t rag-system:latest .

# Image taggen
docker tag rag-system:latest ragsystemacr.azurecr.io/rag-system:latest

# Image pushen
docker push ragsystemacr.azurecr.io/rag-system:latest
```

### 4. Container Apps Environment

```bash
az containerapp env create \
    --name rag-system-env \
    --resource-group rag-system-rg \
    --location westeurope
```

### 5. Container App deployen

```bash
az containerapp create \
    --name rag-system-app \
    --resource-group rag-system-rg \
    --environment rag-system-env \
    --image ragsystemacr.azurecr.io/rag-system:latest \
    --target-port 8501 \
    --ingress external \
    --cpu 2.0 \
    --memory 4.0Gi \
    --min-replicas 1 \
    --max-replicas 10 \
    --env-vars \
        AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
        AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
        AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
        AZURE_AI_SEARCH_SERVICE_NAME="$AZURE_AI_SEARCH_SERVICE_NAME" \
        AZURE_AI_SEARCH_INDEX_NAME="$AZURE_AI_SEARCH_INDEX_NAME" \
        AZURE_AI_SEARCH_API_KEY="$AZURE_AI_SEARCH_API_KEY" \
        AZURE_STORAGE_CONNECTION_STRING="$AZURE_STORAGE_CONNECTION_STRING" \
        AZURE_STORAGE_CONTAINER_NAME="$AZURE_STORAGE_CONTAINER_NAME"
```

## 📈 Skalierung

### Automatische Skalierung

Das System skaliert automatisch basierend auf:
- CPU-Auslastung
- Memory-Auslastung
- Anzahl der Anfragen

### Manuelle Skalierung

```bash
# Skalierung verwalten
./azure-scale.sh

# Oder direkt über Azure CLI
az containerapp update \
    --name rag-system-app \
    --resource-group rag-system-rg \
    --min-replicas 5 \
    --max-replicas 20
```

### Skalierungsregeln anpassen

```bash
# CPU-basierte Skalierung
az containerapp revision set-mode \
    --name rag-system-app \
    --resource-group rag-system-rg \
    --mode multiple

# Custom Skalierungsregeln im Azure Portal konfigurieren
```

## 📊 Monitoring und Logging

### Application Insights

```bash
# Application Insights erstellen
az monitor app-insights component create \
    --app rag-system-insights \
    --location westeurope \
    --resource-group rag-system-rg \
    --application-type web
```

### Logs anzeigen

```bash
# Container App Logs
az containerapp logs show \
    --name rag-system-app \
    --resource-group rag-system-rg \
    --follow

# Application Insights Logs
az monitor app-insights query \
    --app rag-system-insights \
    --analytics-query "traces | where timestamp > ago(1h)"
```

### Metriken überwachen

```bash
# Verfügbare Metriken anzeigen
az monitor metrics list-definitions \
    --resource "/subscriptions/{subscription-id}/resourceGroups/rag-system-rg/providers/Microsoft.App/containerApps/rag-system-app"

# Spezifische Metriken abrufen
az monitor metrics list \
    --resource "/subscriptions/{subscription-id}/resourceGroups/rag-system-rg/providers/Microsoft.App/containerApps/rag-system-app" \
    --metric "CpuPercentage" \
    --interval PT1M
```

## 🔒 Sicherheit

### HTTPS erzwingen

```bash
az containerapp update \
    --name rag-system-app \
    --resource-group rag-system-rg \
    --set-env-vars ENABLE_HTTPS=true
```

### Netzwerk-Sicherheit

```bash
# Private Endpoints für Azure Services
az network private-endpoint create \
    --name rag-system-pe \
    --resource-group rag-system-rg \
    --vnet-name rag-system-vnet \
    --subnet default \
    --private-connection-resource-id "/subscriptions/{subscription-id}/resourceGroups/rag-system-rg/providers/Microsoft.App/containerApps/rag-system-app"
```

### Managed Identity

```bash
# System-assigned Managed Identity aktivieren
az containerapp identity assign \
    --name rag-system-app \
    --resource-group rag-system-rg \
    --system-assigned

# Zugriff auf Azure Blob Storage gewähren
az role assignment create \
    --assignee "system-assigned-managed-identity" \
    --role "Storage Blob Data Contributor" \
    --scope "/subscriptions/{subscription-id}/resourceGroups/rag-system-rg/providers/Microsoft.Storage/storageAccounts/{storage-account-name}"
```

## 🧪 Testing

### Lokales Testing

```bash
# Docker Image lokal testen (Chainlit)
docker run -p 8000:8000 --env-file .env rag-system:latest

# Chainlit App öffnen: http://localhost:8000
```

### Azure Testing

```bash
# Health Check
curl -f https://{app-url}/

# Load Testing
ab -n 1000 -c 10 https://{app-url}/
```

## 🚨 Troubleshooting

### Häufige Probleme

1. **Container startet nicht**
   ```bash
   # Logs überprüfen
   az containerapp logs show --name rag-system-app --resource-group rag-system-rg
   
   # Environment Variables überprüfen
   az containerapp show --name rag-system-app --resource-group rag-system-rg --query "properties.template.containers[0].env"
   ```

2. **Skalierung funktioniert nicht**
   ```bash
   # Revision Mode überprüfen
   az containerapp revision list --name rag-system-app --resource-group rag-system-rg
   
   # Scaling Rules überprüfen
   az containerapp show --name rag-system-app --resource-group rag-system-rg --query "properties.template.scale"
   ```

3. **Performance-Probleme**
   ```bash
   # Metriken überprüfen
   az monitor metrics list --resource "/subscriptions/{subscription-id}/resourceGroups/rag-system-rg/providers/Microsoft.App/containerApps/rag-system-app" --metric "CpuPercentage,MemoryPercentage"
   ```

### Debug-Modus

```bash
# Debug-Logs aktivieren
az containerapp update \
    --name rag-system-app \
    --resource-group rag-system-rg \
    --set-env-vars LOG_LEVEL=DEBUG
```

## 💰 Kostenoptimierung

### Resource Sizing

```bash
# Kleinere Instanzen für Development
az containerapp update \
    --name rag-system-app \
    --resource-group rag-system-rg \
    --cpu 1.0 \
    --memory 2.0Gi \
    --min-replicas 0 \
    --max-replicas 3
```

### Auto-Shutdown

```bash
# Development-Umgebung nachts herunterfahren
az containerapp update \
    --name rag-system-app \
    --resource-group rag-system-rg \
    --min-replicas 0
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
name: Deploy to Azure
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to Azure
      uses: azure/container-apps-deploy-action@v1
      with:
        appSourcePath: '.'
        acrName: 'ragsystemacr'
        acrUsername: ${{ secrets.ACR_USERNAME }}
        acrPassword: ${{ secrets.ACR_PASSWORD }}
        containerAppName: 'rag-system-app'
        resourceGroupName: 'rag-system-rg'
        imageToDeploy: 'ragsystemacr.azurecr.io/rag-system:${{ github.sha }}'
```

## 📚 Weitere Ressourcen

- [Azure Container Apps Dokumentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Azure Monitor Dokumentation](https://docs.microsoft.com/en-us/azure/azure-monitor/)
- [Azure Blob Storage Dokumentation](https://docs.microsoft.com/en-us/azure/storage/blobs/)
- [Streamlit Cloud Deployment](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)

## 🆘 Support

Bei Problemen:
1. Überprüfen Sie die Logs: `./azure-scale.sh` → Option 6
2. Überprüfen Sie die Metriken im Azure Portal
3. Testen Sie lokal mit Docker
4. Überprüfen Sie die Environment Variables

---

**Hinweis**: Dieses Deployment ist für Produktionsumgebungen konfiguriert. Für Development-Umgebungen können Sie die Ressourcen reduzieren.
