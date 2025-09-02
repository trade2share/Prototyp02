#!/bin/bash

# Fix ACR Authentication for existing Container App
echo "🔐 Fixing ACR Authentication for existing Container App..."

# Configuration
RESOURCE_GROUP="Prototyp2"
CONTAINER_APP_NAME="rag-system-app"
ACR_NAME="ragsystem03053"  # Using the existing ACR from your list

echo "📋 Using Resource Group: $RESOURCE_GROUP"
echo "📱 Container App: $CONTAINER_APP_NAME"
echo "🏗️ Container Registry: $ACR_NAME"

# Check if resources exist
if ! az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "❌ Container App $CONTAINER_APP_NAME not found in resource group $RESOURCE_GROUP"
    exit 1
fi

if ! az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "❌ Container Registry $ACR_NAME not found in resource group $RESOURCE_GROUP"
    exit 1
fi

echo "🔑 Getting ACR credentials..."
ACR_LOGIN_SERVER="$ACR_NAME.azurecr.io"
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "username" --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "passwords[0].value" --output tsv)

echo "✅ ACR Username: $ACR_USERNAME"
echo "✅ ACR Login Server: $ACR_LOGIN_SERVER"

echo "🔄 Updating Container App with ACR authentication..."
az containerapp update \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD

echo "✅ ACR Authentication configured successfully!"
echo ""
echo "🔍 Checking Container App status..."
az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "{name:name, provisioningState:properties.provisioningState, image:properties.template.containers[0].image, registry:properties.configuration.registries[0].server}" \
    --output table

echo ""
echo "🌐 Your app should now be accessible at:"
az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv
