#!/usr/bin/env pwsh
# Docker build and Azure Container App deployment script

# Configuration
$resourceGroupName = ""  # You'll be prompted for this
$location = "eastus"      # Default region (will prompt to confirm)
$containerAppName = ""    # You'll be prompted for this
$containerRegistryName = "" # You'll be prompted for this
$imageName = "virtual-try-on"
$imageTag = "latest"

# Check for Azure CLI
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI not found. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Login to Azure if needed
$loginStatus = az account show --query "name" -o tsv 2>$null
if (-not $loginStatus) {
    Write-Host "Please log in to your Azure account"
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to log in to Azure"
        exit 1
    }
}

# Show available subscriptions
Write-Host "Available subscriptions:"
az account list --query "[].{Name:name, ID:id, IsDefault:isDefault}" -o table

# Select subscription
$subscription = Read-Host "Enter the subscription ID or name to use"
az account set --subscription $subscription
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to set subscription"
    exit 1
}

# Get or create resource group
Write-Host "Available resource groups:"
az group list --query "[].name" -o table
$resourceGroupName = Read-Host "Enter resource group name (existing or new)"

# Check if the resource group exists
$groupExists = az group show --name $resourceGroupName 2>$null
if (-not $groupExists) {
    $createGroup = Read-Host "Resource group doesn't exist. Create it? (y/n)"
    if ($createGroup -eq "y") {
        $location = Read-Host "Enter location (e.g., eastus, westus, westeurope)"
        az group create --name $resourceGroupName --location $location
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create resource group"
            exit 1
        }
    } else {
        Write-Error "Resource group not found. Exiting."
        exit 1
    }
}

# Get or create container registry
Write-Host "Available container registries in ${resourceGroupName}:"
az acr list --resource-group $resourceGroupName --query "[].name" -o table
$containerRegistryName = Read-Host "Enter container registry name (existing or new)"

# Check if the container registry exists
$registryExists = az acr show --name $containerRegistryName --resource-group $resourceGroupName 2>$null
if (-not $registryExists) {
    $createRegistry = Read-Host "Container registry doesn't exist. Create it? (y/n)"
    if ($createRegistry -eq "y") {
        az acr create --resource-group $resourceGroupName --name $containerRegistryName --sku Basic --admin-enabled true
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create container registry"
            exit 1
        }
    } else {
        Write-Error "Container registry not found. Exiting."
        exit 1
    }
}

# Log in to container registry
Write-Host "Logging in to container registry..."
az acr login --name $containerRegistryName
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to log in to container registry"
    exit 1
}

# Build and push Docker image
Write-Host "Building and pushing Docker image..."
$acrLoginServer = az acr show --name $containerRegistryName --resource-group $resourceGroupName --query "loginServer" -o tsv
$fullImageName = "$acrLoginServer/$imageName`:$imageTag"

# Build the image
docker build -t $fullImageName .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build Docker image"
    exit 1
}

# Push the image
docker push $fullImageName
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push Docker image"
    exit 1
}

# Get or create container app environment
Write-Host "Checking for Container App Environment..."
$containerAppEnv = az containerapp env list --resource-group $resourceGroupName --query "[0].name" -o tsv 2>$null
if (-not $containerAppEnv) {
    $envName = "$resourceGroupName-env"
    Write-Host "Creating Container App Environment: $envName"
    az containerapp env create --name $envName --resource-group $resourceGroupName --location $location
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create Container App Environment"
        exit 1
    }
    $containerAppEnv = $envName
}

# Create container app name if not provided
if (-not $containerAppName) {
    $containerAppName = "virtual-try-on"
    Write-Host "Using default container app name: $containerAppName"
}

# Ask if Key Vault should be used for secrets
$useKeyVault = Read-Host "Do you want to use Azure Key Vault for secrets? (y/n)"

if ($useKeyVault -eq "y") {
    # Get Key Vault name
    Write-Host "Available Key Vaults:"
    az keyvault list --resource-group $resourceGroupName --query "[].name" -o tsv
    $keyVaultName = Read-Host "Enter Key Vault name (existing or new)"
    
    # Check if the Key Vault exists
    $keyVaultExists = az keyvault show --name $keyVaultName 2>$null
    if (-not $keyVaultExists) {
        $createKeyVault = Read-Host "Key Vault doesn't exist. Create it? (y/n)"
        if ($createKeyVault -eq "y") {
            # Get current user's object ID for access policy
            $currentUser = az ad signed-in-user show --query id -o tsv
            
            Write-Host "Creating Key Vault with access policy for current user..."
            az keyvault create --name $keyVaultName --resource-group $resourceGroupName --location $location --enable-rbac-authorization false
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to create Key Vault"
                exit 1
            }
            
            # Set access policy for the current user
            Write-Host "Setting access policy for current user..."
            az keyvault set-policy --name $keyVaultName --object-id $currentUser --secret-permissions get set list delete
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to set Key Vault access policy"
                exit 1
            }
        } else {
            Write-Error "Key Vault not found. Exiting."
            exit 1
        }
    } else {
        # Set access policy for the current user on existing vault
        $currentUser = az ad signed-in-user show --query id -o tsv
        Write-Host "Setting access policy for current user on existing Key Vault..."
        az keyvault set-policy --name $keyVaultName --object-id $currentUser --secret-permissions get set list delete
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Warning: Could not set access policy on existing Key Vault. You may not have permission to modify it."
            Write-Host "Continuing without Key Vault integration..."
            $useKeyVault = "n"  # Disable Key Vault integration
        }
    }
    
    # Only proceed with adding secrets if we have permission
    if ($useKeyVault -eq "y") {
        # Store secrets in Key Vault
        Write-Host "Adding secrets to Key Vault..."
        try {
            $configPath = Join-Path $pwd "config.json"
            if (Test-Path $configPath) {
                $config = Get-Content $configPath | ConvertFrom-Json
                az keyvault secret set --vault-name $keyVaultName --name "imagegen-aoai-resource" --value $config.imagegen_aoai_resource
                az keyvault secret set --vault-name $keyVaultName --name "imagegen-aoai-endpoint" --value $config.imagegen_aoai_endpoint
                az keyvault secret set --vault-name $keyVaultName --name "imagegen-aoai-deployment" --value $config.imagegen_aoai_deployment
                az keyvault secret set --vault-name $keyVaultName --name "imagegen-aoai-api-key" --value $config.imagegen_aoai_api_key
            } else {
                Write-Host "config.json not found. Please enter the secret values manually."
                $resource = Read-Host "Enter the imagegen_aoai_resource value"
                $endpoint = Read-Host "Enter the imagegen_aoai_endpoint value"
                $deployment = Read-Host "Enter the imagegen_aoai_deployment value"
                $apiKey = Read-Host "Enter the imagegen_aoai_api_key value" -AsSecureString
                $apiKeyPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey))
                
                az keyvault secret set --vault-name $keyVaultName --name "imagegen-aoai-resource" --value $resource
                az keyvault secret set --vault-name $keyVaultName --name "imagegen-aoai-endpoint" --value $endpoint
                az keyvault secret set --vault-name $keyVaultName --name "imagegen-aoai-deployment" --value $deployment
                az keyvault secret set --vault-name $keyVaultName --name "imagegen-aoai-api-key" --value $apiKeyPlain
            }
        } catch {
            Write-Host "Warning: Could not add secrets to Key Vault. Will proceed without Key Vault integration."
            $useKeyVault = "n"  # Disable Key Vault integration
        }
    }
}

# Create or update the container app
$containerAppExists = az containerapp show --name $containerAppName --resource-group $resourceGroupName 2>$null
if ($containerAppExists) {
    Write-Host "Updating existing Container App: $containerAppName"
    
    $updateCmd = "az containerapp update --name $containerAppName --resource-group $resourceGroupName " + `
        "--image $fullImageName " + `
        "--registry-server $acrLoginServer " + `
        "--target-port 8501 " + `
        "--ingress external"
    
    # Add Key Vault integration if selected
    if ($useKeyVault -eq "y") {
        # Create managed identity for the container app if it doesn't exist
        $identityOutput = az containerapp identity show --name $containerAppName --resource-group $resourceGroupName 2>$null
        if (-not $identityOutput) {
            az containerapp identity assign --name $containerAppName --resource-group $resourceGroupName --system-assigned
        }
        
        # Get the principal ID of the container app's managed identity
        $principalId = az containerapp identity show --name $containerAppName --resource-group $resourceGroupName --query "principalId" -o tsv
        
        # Assign Key Vault access policy
        az keyvault set-policy --name $keyVaultName --object-id $principalId --secret-permissions get list
        
        # Update with secrets from Key Vault
        $updateCmd += " --secrets " + `
            "aoai-resource=keyvault:https://$keyVaultName.vault.azure.net/secrets/imagegen-aoai-resource " + `
            "aoai-endpoint=keyvault:https://$keyVaultName.vault.azure.net/secrets/imagegen-aoai-endpoint " + `
            "aoai-deployment=keyvault:https://$keyVaultName.vault.azure.net/secrets/imagegen-aoai-deployment " + `
            "aoai-api-key=keyvault:https://$keyVaultName.vault.azure.net/secrets/imagegen-aoai-api-key"
        
        $updateCmd += " --env-vars " + `
            "imagegen_aoai_resource=secretref:aoai-resource " + `
            "imagegen_aoai_endpoint=secretref:aoai-endpoint " + `
            "imagegen_aoai_deployment=secretref:aoai-deployment " + `
            "imagegen_aoai_api_key=secretref:aoai-api-key"
    }
    
    Invoke-Expression $updateCmd
    
} else {
    Write-Host "Creating new Container App: $containerAppName"
    $registryPassword = az acr credential show --name $containerRegistryName --query "passwords[0].value" -o tsv
    
    # Basic command for creating container app
    $createCmd = "az containerapp create " + `
        "--name $containerAppName " + `
        "--resource-group $resourceGroupName " + `
        "--environment $containerAppEnv " + `
        "--image $fullImageName " + `
        "--registry-server $acrLoginServer " + `
        "--registry-username $containerRegistryName " + `
        "--registry-password $registryPassword " + `
        "--target-port 8501 " + `
        "--ingress external"
    
    # Add Key Vault integration if selected
    if ($useKeyVault -eq "y") {
        # First create the container app without managed identity or secrets
        Invoke-Expression $createCmd
        
        if ($LASTEXITCODE -eq 0) {
            # Now assign system managed identity to the created app
            Write-Host "Assigning system managed identity to Container App..."
            az containerapp identity assign --name $containerAppName --resource-group $resourceGroupName --system-assigned
            
            # Get the principal ID of the container app's managed identity
            $principalId = az containerapp identity show --name $containerAppName --resource-group $resourceGroupName --query "principalId" -o tsv
            
            # Assign Key Vault access policy
            Write-Host "Setting Key Vault access policy for Container App..."
            az keyvault set-policy --name $keyVaultName --object-id $principalId --secret-permissions get list
            
            # Now update the container app with secrets from Key Vault
            Write-Host "Updating Container App with Key Vault secrets..."
            $updateCmd = "az containerapp update --name $containerAppName --resource-group $resourceGroupName " + `
                "--secrets " + `
                "aoai-resource=keyvault:https://$keyVaultName.vault.azure.net/secrets/imagegen-aoai-resource " + `
                "aoai-endpoint=keyvault:https://$keyVaultName.vault.azure.net/secrets/imagegen-aoai-endpoint " + `
                "aoai-deployment=keyvault:https://$keyVaultName.vault.azure.net/secrets/imagegen-aoai-deployment " + `
                "aoai-api-key=keyvault:https://$keyVaultName.vault.azure.net/secrets/imagegen-aoai-api-key " + `
                "--env-vars " + `
                "imagegen_aoai_resource=secretref:aoai-resource " + `
                "imagegen_aoai_endpoint=secretref:aoai-endpoint " + `
                "imagegen_aoai_deployment=secretref:aoai-deployment " + `
                "imagegen_aoai_api_key=secretref:aoai-api-key"
                
            Invoke-Expression $updateCmd
        } else {
            Write-Error "Failed to create Container App"
            exit 1
        }
    } else {
        # No Key Vault integration, just create the container app
        Invoke-Expression $createCmd
    }
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to deploy to Container App"
    exit 1
}

# Show the application URL
$appUrl = az containerapp show --name $containerAppName --resource-group $resourceGroupName --query "properties.configuration.ingress.fqdn" -o tsv
Write-Host "Application deployed successfully!"
Write-Host "Your application is available at: https://$appUrl"

$openBrowser = Read-Host "Open in browser? (y/n)"
if ($openBrowser -eq "y") {
    Start-Process "https://$appUrl"
}
