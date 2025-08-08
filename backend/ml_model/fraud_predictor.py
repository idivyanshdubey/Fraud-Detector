"""
ML-based Fraud Prediction Service
Provides fraud prediction using trained Random Forest model
"""

import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class FraudPredictor:
    def __init__(self, model_path: str = None):
        if model_path is None:
            # Use absolute path relative to this script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, 'fraud_detection_model.pkl')
        
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.feature_columns = []
        
        self.load_model()
    
    def load_model(self):
        """Load the trained model and preprocessing objects"""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.label_encoders = model_data['label_encoders']
                self.feature_columns = model_data['feature_columns']
                logger.info("Fraud detection model loaded successfully")
            else:
                logger.warning(f"Model file not found at {self.model_path}")
                logger.info("Using fallback rule-based detection")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            logger.info("Using fallback rule-based detection")
    
    def extract_features(self, transaction_data: Dict[str, Any]) -> pd.DataFrame:
        """Extract features from transaction data for prediction"""
        
        # Parse timestamp
        try:
            if isinstance(transaction_data.get('timestamp'), str):
                timestamp = datetime.fromisoformat(transaction_data['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()
        except:
            timestamp = datetime.now()
        
        # Extract features
        features = {
            'amount': float(transaction_data.get('amount', 0)),
            'merchant_category_encoded': self._encode_merchant_category(
                transaction_data.get('merchant_category', 'other')
            ),
            'hour_of_day': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'is_weekend': 1 if timestamp.weekday() >= 5 else 0,
            'card_age_days': self._estimate_card_age(transaction_data.get('card_number', '')),
            'avg_transaction_amount': float(transaction_data.get('amount', 0)),  # Simplified
            'transaction_frequency_24h': 1,  # Simplified
            'location_risk_score': self._calculate_location_risk(transaction_data.get('location', {})),
            'merchant_risk_score': self._calculate_merchant_risk(transaction_data.get('merchant', ''))
        }
        
        # Create DataFrame with correct column order
        df = pd.DataFrame([features])[self.feature_columns]
        return df
    
    def _encode_merchant_category(self, category: str) -> int:
        """Encode merchant category using saved label encoder"""
        if 'merchant_category' in self.label_encoders:
            try:
                return self.label_encoders['merchant_category'].transform([category])[0]
            except ValueError:
                # Unknown category, return encoded value for 'other'
                return self.label_encoders['merchant_category'].transform(['other'])[0]
        else:
            # Fallback encoding
            category_map = {
                'grocery': 0, 'gas': 1, 'restaurant': 2, 'retail': 3,
                'online': 4, 'atm': 5, 'other': 6
            }
            return category_map.get(category.lower(), 6)
    
    def _estimate_card_age(self, card_number: str) -> float:
        """Estimate card age based on card number hash (simplified)"""
        # In real implementation, this would query a database
        # For now, use a deterministic but random-looking value
        import hashlib
        card_hash = int(hashlib.md5(card_number.encode()).hexdigest(), 16)
        return (card_hash % 1000) + 30  # 30-1030 days
    
    def _calculate_location_risk(self, location: Dict[str, Any]) -> float:
        """Calculate location-based risk score"""
        if not location:
            return 0.5
        
        # Simplified risk calculation based on coordinates
        lat = location.get('lat', 0)
        lon = location.get('lng', 0) or location.get('lon', 0)
        
        # Risk increases with distance from major cities (simplified)
        risk = abs(lat) * 0.01 + abs(lon) * 0.005
        return min(risk, 1.0)
    
    def _calculate_merchant_risk(self, merchant: str) -> float:
        """Calculate merchant-based risk score"""
        if not merchant:
            return 0.5
        
        # Simplified risk based on merchant name
        import hashlib
        merchant_hash = int(hashlib.md5(merchant.encode()).hexdigest(), 16)
        risk = (merchant_hash % 100) / 100.0
        return risk
    
    def predict(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict fraud probability for a transaction"""
        try:
            # Extract features
            features_df = self.extract_features(transaction_data)
            
            # Scale features
            features_scaled = self.scaler.transform(features_df)
            
            # Make prediction
            fraud_probability = self.model.predict_proba(features_scaled)[0, 1]
            is_fraud = bool(fraud_probability > 0.5)
            
            # Get feature importance for explanation
            feature_importance = dict(zip(
                self.feature_columns,
                self.model.feature_importances_
            ))
            
            return {
                'is_fraud': is_fraud,
                'fraud_probability': float(fraud_probability),
                'confidence': float(abs(fraud_probability - 0.5) * 2),  # 0-1 scale
                'feature_importance': feature_importance,
                'model_used': 'random_forest',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {str(e)}")
            return self._fallback_prediction(transaction_data)
    
    def _fallback_prediction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based prediction when ML model fails"""
        amount = float(transaction_data.get('amount', 0))
        
        # Simple rule-based detection
        is_fraud = amount > 1000
        fraud_probability = 0.85 if is_fraud else 0.15
        
        return {
            'is_fraud': is_fraud,
            'fraud_probability': fraud_probability,
            'confidence': 0.5,
            'feature_importance': {'amount': 1.0},
            'model_used': 'rule_based_fallback',
            'timestamp': datetime.now().isoformat(),
            'note': 'ML model unavailable, using fallback rules'
        }
    
    def batch_predict(self, transactions: list) -> list:
        """Predict fraud for multiple transactions"""
        results = []
        for transaction in transactions:
            result = self.predict(transaction)
            result['transaction_id'] = transaction.get('transaction_id')
            results.append(result)
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        if self.model is None:
            return {
                'status': 'not_loaded',
                'model_type': 'none',
                'features': []
            }
        
        return {
            'status': 'loaded',
            'model_type': 'random_forest',
            'features': self.feature_columns,
            'n_features': len(self.feature_columns),
            'n_estimators': getattr(self.model, 'n_estimators', 'unknown'),
            'feature_importance': dict(zip(
                self.feature_columns,
                self.model.feature_importances_
            )) if hasattr(self.model, 'feature_importances_') else {}
        }

# Global predictor instance
_fraud_predictor = None

def get_fraud_predictor() -> FraudPredictor:
    """Get the global fraud predictor instance"""
    global _fraud_predictor
    if _fraud_predictor is None:
        _fraud_predictor = FraudPredictor()
    return _fraud_predictor
