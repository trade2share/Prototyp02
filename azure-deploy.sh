#!/bin/bash

# Azure RAG System Deployment Script
set -e

echo "🚀 Starting Azure RAG System Deployment..."

# Configuration
RESOURCE_GROUP="rag-system-rg"
LOCATION="westeurope"
# Use existing ACR
ACR_NAME="ragacr1756585434"
CONTAINER_APP_NAME="rag-system-app"
ENVIRONMENT_NAME="rag-system-env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Check environment variables
print_status "Checking environment variables..."
REQUIRED_VARS=("AZURE_OPENAI_API_KEY" "AZURE_OPENAI_ENDPOINT" "AZURE_OPENAI_API_VERSION" "AZURE_AI_SEARCH_SERVICE_NAME" "AZURE_AI_SEARCH_INDEX_NAME" "AZURE_AI_SEARCH_API_KEY" "AZURE_STORAGE_CONNECTION_STRING" "AZURE_STORAGE_CONTAINER_NAME")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        MISSING_VARS+=("$var")
    fi
done

if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
    print_error "Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    print_error "Please set these variables in your .env file or export them:"
    echo "  cp azure-env-template.env .env"
    echo "  nano .env  # Fill in your values"
    echo "  source .env"
    exit 1
fi

print_status "✅ All required environment variables are set"

print_status "Using existing Resource Group: $RESOURCE_GROUP"
# Check if resource group exists
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    print_error "Resource Group $RESOURCE_GROUP not found. Please create it first in Azure Portal."
    exit 1
fi

print_status "Using existing Azure Container Registry: $ACR_NAME"
# Check if ACR exists
if ! az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    print_error "Container Registry $ACR_NAME not found in resource group $RESOURCE_GROUP"
    exit 1
fi

print_status "Getting ACR login server..."
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "loginServer" --output tsv)

print_status "Building and pushing Docker image..."
az acr build --registry $ACR_NAME --image rag-system:latest .

print_status "Creating Container Apps Environment..."
# Check if environment already exists, if yes, delete it
if az containerapp env show --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    print_warning "Deleting existing Container Apps Environment: $ENVIRONMENT_NAME"
    az containerapp env delete --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP --yes
fi
az containerapp env create \
    --name $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

print_status "Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "username" --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "passwords[0].value" --output tsv)

# Verify credentials were retrieved
if [[ -z "$ACR_USERNAME" || -z "$ACR_PASSWORD" ]]; then
    print_error "Failed to retrieve ACR credentials"
    exit 1
fi

print_status "Deploying Container App..."
# Check if container app already exists, if yes, delete it
if az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    print_warning "Deleting existing Container App: $CONTAINER_APP_NAME"
    az containerapp delete --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes
fi
az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image $ACR_LOGIN_SERVER/rag-system:latest \
    --target-port 8000 \
    --ingress external \
    --cpu 2.0 \
    --memory 4.0Gi \
    --min-replicas 1 \
    --max-replicas 10 \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --env-vars \
        AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
        AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
        AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
        AZURE_AI_SEARCH_SERVICE_NAME="$AZURE_AI_SEARCH_SERVICE_NAME" \
        AZURE_AI_SEARCH_INDEX_NAME="$AZURE_AI_SEARCH_INDEX_NAME" \
        AZURE_AI_SEARCH_API_KEY="$AZURE_AI_SEARCH_API_KEY" \
        AZURE_STORAGE_CONNECTION_STRING="$AZURE_STORAGE_CONNECTION_STRING" \
        AZURE_STORAGE_CONTAINER_NAME="$AZURE_STORAGE_CONTAINER_NAME"

print_status "Getting application URL..."
APP_URL=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" --output tsv)

print_status "✅ Deployment completed successfully!"
echo ""
echo "🌐 Application URL: https://$APP_URL"
echo "📊 Monitor your app: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/$CONTAINER_APP_NAME"
echo ""
echo "🔧 To scale your application:"
echo "   az containerapp revision set-mode --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --mode multiple"
echo "   az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --min-replicas 5 --max-replicas 20"
echo ""
echo "📝 To view logs:"
echo "   az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow"
