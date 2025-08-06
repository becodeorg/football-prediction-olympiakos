# Use a lightweight Python image suitable for Azure Functions
# This image is based on Debian, which is a good choice for ODBC dependencies.
FROM mcr.microsoft.com/azure-functions/python:4-python3.10
# Define the working directory in the container
# This is where your function app code will be copied and executed.
WORKDIR /home/site/wwwroot

# Azure Functions expects this environment variable to locate the function app code.
# This is the root directory where your function app code will be located.
ENV AzureWebJobsScriptRoot=/home/site/wwwroot


# Installation of dependancies necessary for pyodbc and SQL Server ODBC driver
# mssql-tools are the Microsoft ODBC drivers and tools for SQL Server
# This will ensure that the ODBC driver is available for pyodbc to connect to SQL

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        apt-transport-https \
        gnupg \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y mssql-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# To check if the file was created correctly
RUN cat /etc/odbcinst.ini

# Register the SQL Server data source name specified in odbc.ini
RUN odbcinst -i -s -f /etc/odbc.ini -l

# Copy requirements.txt to the working directory
# This allows Docker to cache the layer with dependencies if requirements.txt does not change
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# Copy the function app code and host.json into the container
COPY host.json .
COPY function_app.py .
COPY modules ./modules
COPY data ./data
# This is the port that Azure Functions will use to communicate with your app.
# Note: Azure Functions will automatically map this to the appropriate port in the Azure environment.
EXPOSE 80
