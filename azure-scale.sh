#!/bin/bash

# Azure RAG System Scaling Script
set -e

echo "📈 Azure RAG System Scaling Management"

# Configuration
RESOURCE_GROUP="Prototyp2"
CONTAINER_APP_NAME="rag-system-app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Function to show current scaling status
show_status() {
    print_header "Current Scaling Status"
    
    CURRENT_REPLICAS=$(az containerapp show \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "properties.template.scale.minReplicas" \
        --output tsv)
    
    MAX_REPLICAS=$(az containerapp show \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "properties.template.scale.maxReplicas" \
        --output tsv)
    
    echo "Min Replicas: $CURRENT_REPLICAS"
    echo "Max Replicas: $MAX_REPLICAS"
    
    # Show current running instances
    RUNNING_INSTANCES=$(az containerapp replica list \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "length([].{name:name, status:properties.status})" \
        --output tsv)
    
    echo "Currently Running: $RUNNING_INSTANCES instances"
}

# Function to scale up
scale_up() {
    local min_replicas=$1
    local max_replicas=$2
    
    print_header "Scaling Up Application"
    echo "Setting min replicas to: $min_replicas"
    echo "Setting max replicas to: $max_replicas"
    
    az containerapp update \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --min-replicas $min_replicas \
        --max-replicas $max_replicas
    
    print_status "Scaling completed successfully!"
}

# Function to scale down
scale_down() {
    local min_replicas=$1
    local max_replicas=$2
    
    print_header "Scaling Down Application"
    echo "Setting min replicas to: $min_replicas"
    echo "Setting max replicas to: $max_replicas"
    
    az containerapp update \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --min-replicas $min_replicas \
        --max-replicas $max_replicas
    
    print_status "Scaling completed successfully!"
}

# Function to enable auto-scaling
enable_autoscaling() {
    print_header "Enabling Auto-Scaling"
    
    # Enable multiple revision mode for better scaling
    az containerapp revision set-mode \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --mode multiple
    
    print_status "Auto-scaling enabled!"
    print_warning "Note: You may need to configure custom scaling rules in Azure Portal for advanced auto-scaling"
}

# Function to set custom scaling rules
set_custom_scaling() {
    print_header "Setting Custom Scaling Rules"
    
    echo "Available scaling options:"
    echo "1. CPU-based scaling (default)"
    echo "2. Memory-based scaling"
    echo "3. Custom metric scaling"
    echo "4. Schedule-based scaling"
    
    read -p "Choose scaling option (1-4): " choice
    
    case $choice in
        1)
            print_status "CPU-based scaling is already enabled by default"
            ;;
        2)
            print_warning "Memory-based scaling requires custom configuration in Azure Portal"
            ;;
        3)
            print_warning "Custom metric scaling requires custom configuration in Azure Portal"
            ;;
        4)
            print_warning "Schedule-based scaling requires custom configuration in Azure Portal"
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

# Function to monitor scaling
monitor_scaling() {
    print_header "Monitoring Scaling Activity"
    
    echo "Showing recent scaling events..."
    az containerapp logs show \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --follow \
        --max-length 100
}

# Main menu
main_menu() {
    while true; do
        echo ""
        print_header "Azure RAG System Scaling Menu"
        echo "1. Show current scaling status"
        echo "2. Scale up (increase replicas)"
        echo "3. Scale down (decrease replicas)"
        echo "4. Enable auto-scaling"
        echo "5. Set custom scaling rules"
        echo "6. Monitor scaling activity"
        echo "7. Exit"
        
        read -p "Choose an option (1-7): " choice
        
        case $choice in
            1)
                show_status
                ;;
            2)
                read -p "Enter min replicas: " min_replicas
                read -p "Enter max replicas: " max_replicas
                scale_up $min_replicas $max_replicas
                ;;
            3)
                read -p "Enter min replicas: " min_replicas
                read -p "Enter max replicas: " max_replicas
                scale_down $min_replicas $max_replicas
                ;;
            4)
                enable_autoscaling
                ;;
            5)
                set_custom_scaling
                ;;
            6)
                monitor_scaling
                ;;
            7)
                print_status "Exiting scaling management..."
                exit 0
                ;;
            *)
                print_error "Invalid option. Please choose 1-7."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Check if Azure CLI is installed and logged in
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Start main menu
main_menu
