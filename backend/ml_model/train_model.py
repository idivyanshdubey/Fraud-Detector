"""
Fraud Detection ML Model Training Script
Trains and saves a Random Forest model for fraud detection
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
import os
from datetime import datetime

class FraudModelTrainer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = [
            'amount', 'merchant_category_encoded', 'hour_of_day', 
            'day_of_week', 'is_weekend', 'card_age_days',
            'avg_transaction_amount', 'transaction_frequency_24h',
            'location_risk_score', 'merchant_risk_score'
        ]
    
    def generate_synthetic_data(self, n_samples=10000):
        """Generate synthetic fraud detection training data"""
        np.random.seed(42)
        
        # Generate base features
        data = {
            'transaction_id': [f'txn_{i:08d}' for i in range(n_samples)],
            'amount': np.random.lognormal(4.5, 1.5, n_samples),
            'merchant_category': np.random.choice([
                'grocery', 'gas', 'restaurant', 'retail', 'online', 'atm', 'other'
            ], n_samples),
            'hour_of_day': np.random.randint(0, 24, n_samples),
            'day_of_week': np.random.randint(0, 7, n_samples),
            'is_weekend': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
            'card_age_days': np.random.exponential(365, n_samples),
            'avg_transaction_amount': np.random.lognormal(4.0, 1.0, n_samples),
            'transaction_frequency_24h': np.random.poisson(2, n_samples),
            'location_risk_score': np.random.beta(2, 5, n_samples),
            'merchant_risk_score': np.random.beta(3, 4, n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Create fraud labels based on patterns
        fraud_probability = (
            (df['amount'] > 1000).astype(int) * 0.3 +
            (df['transaction_frequency_24h'] > 5).astype(int) * 0.2 +
            (df['location_risk_score'] > 0.7).astype(int) * 0.2 +
            (df['merchant_risk_score'] > 0.8).astype(int) * 0.2 +
            np.random.random(n_samples) * 0.1
        )
        
        df['is_fraud'] = (fraud_probability > 0.5).astype(int)
        
        # Add some realistic fraud patterns
        fraud_indices = df[df['is_fraud'] == 1].index
        df.loc[fraud_indices, 'amount'] *= np.random.uniform(2, 10, len(fraud_indices))
        df.loc[fraud_indices, 'transaction_frequency_24h'] += np.random.randint(3, 10, len(fraud_indices))
        
        return df
    
    def preprocess_data(self, df):
        """Preprocess data for training"""
        # Encode categorical variables
        le = LabelEncoder()
        df['merchant_category_encoded'] = le.fit_transform(df['merchant_category'])
        self.label_encoders['merchant_category'] = le
        
        # Create feature matrix
        X = df[self.feature_columns]
        y = df['is_fraud']
        
        return X, y
    
    def train_model(self, X_train, y_train):
        """Train the fraud detection model"""
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Define parameter grid for tuning
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [10, 15, None],
            'min_samples_split': [2, 5],
            'min_samples_leaf': [1, 2]
        }
        
        # Create and train model
        rf_model = RandomForestClassifier(random_state=42, class_weight='balanced')
        
        # Use GridSearchCV for hyperparameter tuning
        grid_search = GridSearchCV(
            rf_model, param_grid, cv=3, scoring='roc_auc', n_jobs=-1, verbose=1
        )
        
        grid_search.fit(X_train_scaled, y_train)
        
        self.model = grid_search.best_estimator_
        print(f"Best parameters: {grid_search.best_params_}")
        
        return self.model
    
    def evaluate_model(self, X_test, y_test):
        """Evaluate model performance"""
        X_test_scaled = self.scaler.transform(X_test)
        
        # Make predictions
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # Calculate metrics
        accuracy = (y_pred == y_test).mean()
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        print("Model Performance:")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"ROC-AUC: {roc_auc:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        return {
            'accuracy': accuracy,
            'roc_auc': roc_auc,
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }
    
    def save_model(self, model_path=None):
        """Save the trained model and preprocessing objects"""
        if model_path is None:
            # Use absolute path relative to this script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, 'fraud_detection_model.pkl')
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns,
            'training_date': datetime.now().isoformat()
        }
        
        # Ensure directory exists
        model_dir = os.path.dirname(model_path)
        if model_dir and not os.path.exists(model_dir):
            os.makedirs(model_dir, exist_ok=True)
            
        joblib.dump(model_data, model_path)
        print(f"Model saved to {model_path}")
    
    def load_model(self, model_path='fraud_detection_model.pkl'):
        """Load a trained model"""
        model_data = joblib.load(model_path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoders = model_data['label_encoders']
        self.feature_columns = model_data['feature_columns']
        print(f"Model loaded from {model_path}")
    
    def run_training_pipeline(self):
        """Complete training pipeline"""
        print("Starting fraud detection model training...")
        
        # Generate training data
        df = self.generate_synthetic_data(10000)
        print(f"Generated {len(df)} training samples")
        print(f"Fraud rate: {(df['is_fraud'].sum() / len(df) * 100):.2f}%")
        
        # Preprocess data
        X, y = self.preprocess_data(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Train model
        self.train_model(X_train, y_train)
        
        # Evaluate model
        metrics = self.evaluate_model(X_test, y_test)
        
        # Save model
        self.save_model()
        
        return metrics

if __name__ == "__main__":
    trainer = FraudModelTrainer()
    trainer.run_training_pipeline()
