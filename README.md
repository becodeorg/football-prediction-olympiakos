# **Football Prediction Project - Olympiakos**

A comprehensive machine learning platform for predicting football match outcomes, built on Azure infrastructure using Azure Functions and containerized deployments.

## 🎯 **Project Overview**

This project implements an end-to-end machine learning pipeline for football match prediction, specifically focusing on Belgian Jupiler League data. The system automatically ingests match data, processes it, trains prediction models, and provides API endpoints for predictions and data management.

## 🏗️ **Architecture**

The project consists of several key components:

### **Infrastructure (Terraform)**
- **Azure Resource Group**: Contains all project resources
- **Azure SQL Database**: Stores football match data and statistics
- **Azure Container Registry (ACR)**: Hosts Docker images for the function app
- **Azure Functions**: Serverless compute for API endpoints and ML operations
- **Azure Storage Account**: Blob storage for ML models and logs
- **Application Insights**: Monitoring and logging

### Application Components

#### **1. API Layer (`src/api/function_app.py`)**
Azure Functions providing REST endpoints:

- `GET /api/test` - Health check endpoint
- `GET /api/get_datas` - Retrieve football match data with CSV-formatted column names
- `POST /api/upload_football_matches_csv` - Upload CSV data to database
- `POST /api/predict` - Make predictions using trained ML models
- `POST /api/models/train` - Manually trigger model training
- **Timer Function** - Automated data synchronization (runs every monday at 1AM)

#### **2. Data Processing Pipeline**

**DataLoader** (`src/api/modules/loader/DataLoader.py`)
- Fetches CSV data from external sources (football-data.co.uk)
- Loads data from Azure SQL Database
- Handles data format conversion and validation

**DataProcessor** (`src/api/modules/processor/DataProcessor.py`)
- Feature engineering for team statistics (goals, win rates, shots on target)
- Data preprocessing and normalization
- Train/test data splitting

#### **3. Machine Learning Pipeline**

**AbstractModel** (`src/api/modules/model/AbstractModel.py`)
- Base class defining the ML model interface

**LinRegModel** (`src/api/modules/model/LinRegModel.py`)
- Logistic Regression implementation for match outcome prediction
- Supports multi-class classification (Home Win/Draw/Away Win)
- Performance metrics calculation

**ModelBlobStorage** (`src/api/modules/ModelBlobStorage.py`)
- Manages ML model persistence in Azure Blob Storage
- Handles model versioning and metadata

## 🔄 **Data Flow**

1. **Data Ingestion**: Timer function automatically fetches latest match data from external CSV sources
2. **Data Processing**: Raw CSV data is cleaned, validated, and stored in Azure SQL Database
3. **Feature Engineering**: Historical team statistics are calculated for prediction features
4. **Model Training**: When new data is available, ML models are retrained automatically
5. **Model Storage**: Trained models are versioned and stored in Azure Blob Storage
6. **Predictions**: API endpoints serve real-time predictions using the latest trained model

## 🚀 **Deployment**

The project uses Infrastructure as Code (IaC) with Terraform for automated deployment:

### **Prerequisites**
- Azure CLI installed and configured
- Terraform >= 1.0
- Docker Desktop
- SQL Server command-line tools (sqlcmd)

### **Deployment Steps**

1. **Deploy Infrastructure**:
```bash
terraform init
terraform plan --out main.tfplan
terraform apply "main.tfplan"
```

2. **Build and Push Docker Image**:
```powershell
.\build_push_image.ps1 -ResourceGroupName "OlympiakosGroup" -FunctionAppName "olympiakos" -DockerImageTag "dev"
```
This script will build and push image to Azure Container registry

3. **Run Locally (Optional)**:
```powershell
.\run_local.ps1
```
You will be prompt to give resources informations (Resource group, app name, app version, connection string,...)


## 🐳 **Containerization**

The application is fully containerized using Docker:

- **Base Image**: `mcr.microsoft.com/azure-functions/python:4-python3.10`
- **Dependencies**: Includes ODBC drivers for SQL Server connectivity
- **Container Registry**: Azure Container Registry for image storage
- **Deployment**: Azure Functions with container deployment

## 📊 **Data Schema**

The system processes football match data with the following key attributes:

- **Match Information**: Date, time, teams, division
- **Match Results**: Full-time and half-time scores and results
- **Statistics**: Shots, fouls, corners, cards for both teams
- **Betting Odds**: Various betting market odds for prediction features

## 🔧 **Configuration**

Key configuration files:

- `local.settings.json` - Local development settings
- `host.json` - Azure Functions configuration
- `requirements.txt` - Python dependencies
- `variables.tf` - Terraform variable definitions

## 📈 **Monitoring**

- **Application Insights**: Performance monitoring and error tracking
- **Azure Function Logs**: Detailed execution logs
- **SQL Database Metrics**: Database performance monitoring

## 🔐 **Security**

- **Managed Identity**: Secure access to Azure resources
- **SQL Firewall Rules**: Restricted database access
- **Connection Strings**: Secure storage of credentials
- **Private Blob Storage**: Restricted access to ML models

## 🧪 **Testing**

Test files located in `src/test/`:
- `test_api.py` - API endpoint testing

## 📝 **Usage Examples**

### **Upload Match Data**
```bash
curl -X POST -H "Content-Type: text/csv" --data-binary @match_data.csv http://localhost:7071/api/upload_football_matches_csv
```

### **Get Match Data**
```bash
curl -X GET http://localhost:7071/api/get_datas
```

### **Make Prediction**
```bash
curl -X POST -H "Content-Type: application/json" -d '{"HomeTeam": "...","AwayTeam":"...","Date":"..."}' http://localhost:7071/api/predict
```

## 🤝 **Contributing**

 **Project team members:** 

- ##### *Data Analyst*   : [**Elsarrive**](https://github.com/elsarrive)
- ##### *Data Scientist* : [**DieuHang88**](https://github.com/dieuhang88)
- ##### *Data Scientist* : [**Olessia179**](https://github.com/olesia179)
- ##### *Data Engineer*  : [**Fillinger66**](https://github.com/Fillinger66)
