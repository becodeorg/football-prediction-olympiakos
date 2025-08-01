# --- Configuration ---
# Variables are passed as command line parameters
# This script is used to run the Azure Function App locally using Docker

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,

    [Parameter(Mandatory=$true)]
    [string]$FunctionAppName,

    [Parameter(Mandatory=$true)]
    [string]$DockerImageTag,

    [Parameter(Mandatory=$true)]
    [string]$SqlConnectionStringOdbc,

    [Parameter(Mandatory=$true)]
    [string]$AzureWebJobsStorage,

    [Parameter(Mandatory=$true)]
    [string]$ApplicationInsightsConnectionString
)

# Check if Docker is running
Write-Host "Check docker state..."

try {
    docker info | Out-Null
} catch {
    Write-Error "Error: Docker isn't running or not accessible. Please start Docker Desktop."
    exit 1
}
Write-Host "Docker is currently running."

# Fetch the ACR login server for the Function App
Write-Host "--- Step 1: Fetching ACR Information ---"
Write-Host "Fetching ACR login server for Function App: $($FunctionAppName)acr in Resource Group: $($ResourceGroupName)"
try {
    $AcrLoginServer = (az acr show --name "$($FunctionAppName)acr" --query loginServer --resource-group "$($ResourceGroupName)" -o tsv)
} catch {
    Write-Error "Error: Unable to retrieve ACR login server. Check the resource group and Function App name, and ensure Azure CLI is logged in."
    exit 1
}

if ([string]::IsNullOrEmpty($AcrLoginServer)) {
    Write-Error "Error: ACR login server is empty. Check the resource group and Function App name."
    exit 1
}
Write-Host "ACR login server: $($AcrLoginServer)"

# Note: Docker repository names are case-insensitive, but it's a good practice to use lowercase.
# This ensures consistency and avoids potential issues with case sensitivity.
$DockerRepositoryName = $FunctionAppName.ToLowerInvariant()

$ImageFullName = "$($AcrLoginServer)/$($DockerRepositoryName):$($DockerImageTag)"

Write-Host "--- Step 2: Launching Docker Container Locally ---"
Write-Host "Launching image: $($ImageFullName) on local port 8080"

# Command docker run
# -p 8080:80 map the container's port 80 to the local port 8080
# -e sets environment variables in the container
# --rm automatically removes the container when it stops
# -it allows interactive output and stopping with Ctrl+C
try {
    docker run -p 8080:80 `
        -e "FUNCTIONS_WORKER_RUNTIME=python" `
        -e "FUNCTIONS_EXTENSION_VERSION=~4" `
        -e "SQL_CONNECTION_STRING_ODBC=$SqlConnectionStringOdbc" `
        -e "AzureWebJobsStorage=$AzureWebJobsStorage" `
        -e "APPLICATIONINSIGHTS_CONNECTION_STRING=$ApplicationInsightsConnectionString" `
        --rm -it "$($ImageFullName)"
} catch {
    Write-Error "Error: Failed to launch Docker container. Details: $($_.Exception.Message)"
    exit 1
}

Write-Host "Docker container stopped."
Write-Host "Script completed."
