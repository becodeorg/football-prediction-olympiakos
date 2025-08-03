# --- Configuration ---
# Variables for the Azure Function App and Docker image

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,

    [Parameter(Mandatory=$true)]
    [string]$FunctionAppName,

    [Parameter(Mandatory=$true)]
    [string]$DockerImageTag
)


# Verify if Docker is running
Write-Host "Docker state check..."
try {
    docker info | Out-Null
} catch {
    Write-Error "Error: Docker isn't in execution or not accessible. Please start docker first."
    exit 1
}
Write-Host "Docker is currently running."

# --- Récupérer les informations de l'ACR via Azure CLI ---
# Fetch the ACR login server for the Function App
Write-Host "--- Step 1: Retreive ACR informations ---"
Write-Host "Retrieve ACR server connection for Azure App function: $($FunctionAppName)acr in resource group: $($ResourceGroupName)"
try {
    $AcrLoginServer = (az acr show --name "$($FunctionAppName)acr" --query loginServer --resource-group "$($ResourceGroupName)" -o tsv)
} catch {
    Write-Error "Erreur: Impossible de récupérer le serveur de connexion ACR. Vérifiez le nom du groupe de ressources et de la Function App, et assurez-vous que Azure CLI est connecté."
    Write-Error "Error: Impossible to retrieve ACR connection server. Check function group and azure function app and validate that Azure CLI is connected."
    exit 1
}

if ([string]::IsNullOrEmpty($AcrLoginServer)) {
    Write-Error "Error: ACR connection server is empty. Check function group and azure function app."
    exit 1
}
Write-Host "ACR connection server: $($AcrLoginServer)"

$ImageFullName = "$($AcrLoginServer)/$($FunctionAppName):$($DockerImageTag)"

# --- Path to Dockerfile ---
$DockerfileContextPath = "src/api"

# --- Build Docker image ---
Write-Host "--- Build Docker image ---"
Write-Host "Building image: $($ImageFullName) from context: $($DockerfileContextPath)"
try {
    docker build --no-cache -t "$($ImageFullName)" "$($DockerfileContextPath)"
} catch {
    Write-Error "Error: Docker image build failed. Details: $($_.Exception.Message)"
    exit 1
}
Write-Host "Docker image built successfully."
