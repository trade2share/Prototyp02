#!/bin/bash

# Docker Build and Push Script for Azure Container Registry
# Usage: ./docker-build-push.sh [registry-name] [image-tag]

set -e

# Default values
REGISTRY_NAME=${1:-"your-registry-name"}
IMAGE_TAG=${2:-"latest"}
IMAGE_NAME="rag-prototyp"
FULL_IMAGE_NAME="${REGISTRY_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

echo "🚀 Starting Docker build and push process..."
echo "Registry: ${REGISTRY_NAME}.azurecr.io"
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "🔐 Please log in to Azure first:"
    echo "az login"
    exit 1
fi

echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
else
    echo "❌ Docker build failed!"
    exit 1
fi

echo "🏷️  Tagging image for Azure Container Registry..."
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${FULL_IMAGE_NAME}

echo "🔐 Logging in to Azure Container Registry..."
az acr login --name ${REGISTRY_NAME}

if [ $? -eq 0 ]; then
    echo "✅ Successfully logged in to ACR!"
else
    echo "❌ Failed to log in to ACR!"
    exit 1
fi

echo "📤 Pushing image to Azure Container Registry..."
docker push ${FULL_IMAGE_NAME}

if [ $? -eq 0 ]; then
    echo "✅ Image pushed successfully to ${FULL_IMAGE_NAME}!"
    echo ""
    echo "🎉 Deployment complete! You can now deploy this image to Azure Container Instances or AKS."
    echo ""
    echo "To run the container locally:"
    echo "docker run -p 8501:8501 ${FULL_IMAGE_NAME}"
    echo ""
    echo "To deploy to Azure Container Instances:"
    echo "az container create --resource-group your-rg --name rag-prototyp --image ${FULL_IMAGE_NAME} --ports 8501 --dns-name-label your-dns-label"
else
    echo "❌ Failed to push image to ACR!"
    exit 1
fi
