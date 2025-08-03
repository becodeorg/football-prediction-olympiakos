import os
import json
import pickle
import logging
from io import BytesIO
from datetime import datetime
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import logging

# ==============================================
# Blob Storage Helper Class
# ==============================================
class ModelBlobStorage:
    def __init__(self):
        # Use connection string for authentication (simpler for demo)
        self.connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
        self.models_container = os.environ.get('MODELS_CONTAINER_NAME', 'models')
        
        if not self.connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable is required")
        
        # Create blob service client
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
    
    def save_model(self, model, model_metadata: dict, model_name: str, version: str = None) -> str:
        """
        Save a model to blob storage
        
        Args:
            model: The model object to save (sklearn, joblib, pickle-compatible)
            model_name: Name of the model
            version: Version string (optional, defaults to timestamp)
            
        Returns:
            str: Blob name of the saved model
        """
        try:
            # Generate version if not provided
            logging.debug(f"ModelBlobStorage::save_model -> Saving model '{model_name}' version '{version}' to blob storage...")
            if not version:
                version = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            #blob_name = f"{model_name}_v{version}.pkl"
            blob_name = f"{model_name}.pkl"
            logging.debug(f"ModelBlobStorage::save_model ->Blob name: {blob_name}")

            # Create a complete model package
            model_package = {
                "model": model,
                "metadata": model_metadata,
                "version": version,
                "saved_at": datetime.now().isoformat()
            }

            # Prepare blob metadata (must be strings)
            blob_metadata = {}
            for key, value in model_metadata.items():
                # Convert all values to strings for blob metadata
                blob_metadata[key] = str(value)
            
            # Add additional metadata
            blob_metadata.update({
                "model_name": model_name,
                "version": version,
                "upload_date": datetime.now().isoformat()
            })

            # Serialize model to bytes
            model_bytes = pickle.dumps(model_package)
            logging.debug(f"ModelBlobStorage::save_model -> Model serialized to bytes: {len(model_bytes)} bytes")
            # Upload to blob storage
            logging.debug(f"ModelBlobStorage::save_model -> Uploading model to blob storage in container '{self.models_container}'...")
            blob_client = self.blob_service_client.get_blob_client(
                container=self.models_container,
                blob=blob_name
            )
            logging.debug(f"ModelBlobStorage::save_model -> Uploading model to blob storage in container '{self.models_container}'...")
            blob_client.upload_blob(
                data=model_bytes,
                overwrite=True,
                metadata=blob_metadata
            )
            
            logging.debug(f"ModelBlobStorage::save_model -> Model saved successfully: {blob_name}")
            return blob_name
            
        except Exception as e:
            logging.error(f"Error saving model: {str(e)}")
            raise
    
    def load_model(self, blob_name: str):
        """
        Load a model from blob storage
        
        Args:
            blob_name: Name of the blob containing the model
            
        Returns:
            The deserialized model object
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.models_container,
                blob=blob_name
            )
            
            # Download blob data
            blob_data = blob_client.download_blob().readall()
            
            # Deserialize model
            model = pickle.loads(blob_data)
            
            logging.info(f"Model loaded successfully: {blob_name}")
            return model
            
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            raise
    
    def list_models(self, model_name_prefix: str = None) -> list:
        """
        List all models in blob storage
        
        Args:
            model_name_prefix: Filter by model name prefix (optional)
            
        Returns:
            list: List of model information dictionaries
        """
        try:
            container_client = self.blob_service_client.get_container_client(
                self.models_container
            )
            
            models = []
            for blob in container_client.list_blobs(include=['metadata']):
                if model_name_prefix and not blob.name.startswith(model_name_prefix):
                    continue
                    
                models.append({
                    "blob_name": blob.name,
                    "size_bytes": blob.size,
                    "last_modified": blob.last_modified.isoformat(),
                    "metadata": blob.metadata or {}
                })
            
            return models
            
        except Exception as e:
            logging.error(f"Error listing models: {str(e)}")
            raise
    
    def delete_model(self, blob_name: str) -> bool:
        """
        Delete a model from blob storage
        
        Args:
            blob_name: Name of the blob to delete
            
        Returns:
            bool: True if successful
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.models_container,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            logging.info(f"Model deleted successfully: {blob_name}")
            return True
            
        except Exception as e:
            logging.error(f"Error deleting model: {str(e)}")
            raise