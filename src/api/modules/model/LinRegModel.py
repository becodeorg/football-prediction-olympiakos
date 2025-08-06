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

    def __init__(self,model=None):
        super().__init__()
        if model is not None:
            self.model = model
        else:
            self.model = LogisticRegression(C=0.08858667904100823, max_iter=1000, penalty='l1', solver='saga')

    def train(self, X_train, X_test, y_train, y_test,assess_predictions=True):
        """
        Train the linear regression model using the provided training data.
        """
        # Dictionary to store model performance
        performance = {}

        self.model.fit(X_train, y_train)
        
        if not assess_predictions:
            return

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
                brier = brier_score_loss(y_test, y_proba, labels=[-1, 0, 1])
            except Exception as e:
                print(f"Error calculating logloss or Brier for LogisticRegression: {e}")

        performance = {
            'Accuracy': "{:.5f}".format(accuracy),
            'Precision': "{:.5f}".format(precision),
            'Recall': "{:.5f}".format(recall),
            'F1-Score': "{:.5f}".format(f1),
            'LogLoss': "{:.5f}".format(logloss),
            'BrierScore': "{:.5f}".format(brier)
        }

        # Print classification report
        logging.info(f"\nClassification Report for LogisticRegression:\n")
        logging.info("\n"+classification_report(y_test, y_pred, target_names=[['Loss', 'Draw', 'Win'][c + 1] for c in self.model.classes_]))

        # 6. Model Evaluation
        logging.info("\nModel Performance Summary:\n"+json.dumps(performance, indent=4))
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
    
    def predict(self, samples):
        """
        Predict the outcomes using the trained model.
        :param X: Input features for prediction.
        :return: Predicted outcomes.
        """
        results = []
        for sample in samples: # sample - pd.DataFrame
            # Predict generally returns 2 outcomes: for homeTeam - awayTeam and awayTeam - hometeam
            logging.info(f"Predicting for sample: {sample}")
            result = self.model.predict_proba(sample)
            if sample.shape[0] == 2:
                # Reverse the order for venue = 0 (first prediction) due to Loss = -1, Draw = 0, Win = 1
                result[0] = np.flip(result[0])
                # Average the results for both predictions
                results.append(np.mean(result, axis = 0))
            elif sample.shape[0] == 1:
                if int(sample.iloc[0]['venue']) == 0:
                    result[0] = np.flip(result[0])
                results.append(result[0])
            else:
                results.append(np.array([]))
                
        return results