from modules.model.AbstractModel import AbstractModel
from sklearn.metrics import brier_score_loss, classification_report, f1_score, log_loss, precision_score, recall_score, accuracy_score
from sklearn.linear_model import LogisticRegression
import pandas as pd
import numpy as np
import logging
import json

class LinRegModel (AbstractModel):
    """
    Linear Regression Model for predicting match outcomes.
    This class implements the train method to fit a linear regression model.
    """

    def __init__(self):
        super().__init__()
        self.model = LogisticRegression(multi_class='multinomial', max_iter=1000, random_state=42)

    def train(self, X_train, X_test, y_train, y_test):
        """
        Train the linear regression model using the provided training data.
        """
        # Dictionary to store model performance
        performance = {}

        #self.model = LogisticRegression(multi_class='multinomial', max_iter=1000, random_state=42)
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)

        # For log loss and brier score, we need predicted probabilities
        if hasattr(self.model, "predict_proba"):
            y_proba = self.model.predict_proba(X_test)
        else:
            y_proba = None  # Some models might not support predict_proba

        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

        # Initialize defaults
        logloss = None
        brier = None

        # Log loss requires probabilities and multi-class support
        if y_proba is not None:
            try:
                logloss = log_loss(y_test, y_proba)
                # Brier score is typically used for binary classification, but we can calculate it for each class and average
                if y_proba.shape[1] == 3:
                    y_test_bin = np.eye(3)[y_test]
                    brier = np.mean([
                        brier_score_loss(y_test_bin[:, i], y_proba[:, i])
                        for i in range(3)
                    ])
            except Exception as e:
                logging.info(f"LinRegModel::train -> Error calculating logloss or Brier for LogisticRegression: {e}")

        performance= {
            'Accuracy': accuracy,
            'Precision': precision,
            'Recall': recall,
            'F1-Score': f1,
            'LogLoss': logloss,
            'BrierScore': brier
        }

        # Print classification report
        logging.info(f"LinRegModel::train -> \nClassification Report for LogisticRegression:\n")
        logging.info("LinRegModel::train -> \n"+classification_report(y_test, y_pred, target_names=['Away Win', 'Draw', 'Home Win']))
        # 6. Model Evaluation
        logging.info("\nLinRegModel::train -> Model Performance Summary:\n"+json.dumps(performance, indent=4))
        return performance

        

    def save_model_to_blob(self, blob_storage_path, file_name):
        """
        Save the trained model to a file.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")
    def load_model_from_blob(self, blob_storage_path, file_name):
        """
        Load a trained model from a file.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")
    
    def predict(self, X):
        """
        Predict the outcomes using the trained model.
        :param X: Input features for prediction.
        :return: Predicted outcomes.
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet.")
        
        return self.model.predict(X)