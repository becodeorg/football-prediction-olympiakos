from abc import ABC, abstractmethod


class AbstractModel(ABC):
    """
    Abstract base class for data models.
    This class serves as a template for creating specific data models.
    """

    def __init__(self):
        super().__init__()
        self.model = None
        
    @abstractmethod
    def train(self,X_train, X_test, y_train, y_test):
        """
        Load data into the model.
        This method should be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def save_model_to_blob(self, blob_storage_path, file_name):
        """
        Save the trained model to a file.
        This method should be implemented by subclasses.
        """
        pass
    @abstractmethod
    def load_model_from_blob(self, blob_storage_path, file_name):
        """
        Load a trained model from a file.
        This method should be implemented by subclasses.
        """
        pass