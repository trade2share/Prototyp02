#!/bin/bash

# Quick Azure RAG System Deployment
echo "🚀 Quick Azure RAG System Deployment"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Install it first: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check login
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Run 'az login' first."
    exit 1
fi

# Configuration
RG="Prototyp2"
LOCATION="westeurope"
# Generate unique ACR name with timestamp
ACR="ragsystem$(date +%s | tail -c 6)"
APP="rag-system-app"
ENV="rag-system-env"

echo "📋 Using existing Resource Group: $RG"
# Check if resource group exists
if ! az group show --name $RG &> /dev/null; then
    echo "❌ Resource Group $RG not found. Please create it first in Azure Portal."
    exit 1
fi

echo "🏗️ Creating Container Registry: $ACR"
# Check if ACR already exists, if yes, delete it
if az acr show --name $ACR --resource-group $RG &> /dev/null; then
    echo "🗑️ Deleting existing Container Registry: $ACR"
    az acr delete --name $ACR --resource-group $RG --yes
fi
az acr create --resource-group $RG --name $ACR --sku Basic --admin-enabled true

echo "🐳 Building and pushing Docker image..."
az acr build --registry $ACR --image rag-system:latest .

echo "🌍 Creating Container Apps Environment..."
# Check if environment already exists, if yes, delete it
if az containerapp env show --name $ENV --resource-group $RG &> /dev/null; then
    echo "🗑️ Deleting existing Container Apps Environment: $ENV"
    az containerapp env delete --name $ENV --resource-group $RG --yes
fi
az containerapp env create --name $ENV --resource-group $RG --location $LOCATION

echo "🔐 Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name $ACR --resource-group $RG --query "username" --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR --resource-group $RG --query "passwords[0].value" --output tsv)

echo "📱 Deploying Container App..."
# Check if container app already exists, if yes, delete it
if az containerapp show --name $APP --resource-group $RG &> /dev/null; then
    echo "🗑️ Deleting existing Container App: $APP"
    az containerapp delete --name $APP --resource-group $RG --yes
fi
az containerapp create \
    --name $APP \
    --resource-group $RG \
    --environment $ENV \
    --image $ACR.azurecr.io/rag-system:latest \
    --target-port 8501 \
    --ingress external \
    --cpu 2.0 \
    --memory 4.0Gi \
    --min-replicas 1 \
    --max-replicas 10 \
    --registry-server $ACR.azurecr.io \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD

echo "✅ Deployment completed!"
echo "🌐 Your app is available at:"
az containerapp show --name $APP --resource-group $RG --query "properties.configuration.ingress.fqdn" --output tsv
