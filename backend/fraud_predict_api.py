from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os
import requests
import json

# Add ml_model to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_model.fraud_predictor import get_fraud_predictor

app = FastAPI(
    title="ML Fraud Detection API",
    description="Advanced fraud detection using machine learning models",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TransactionData(BaseModel):
    transaction_id: str
    amount: float
    merchant: str
    card_number: str
    timestamp: str
    location: dict = {"lat": 0.0, "lng": 0.0}
    customer_id: str
    category: Optional[str] = "unknown"
    merchant_category: Optional[str] = "unknown"

class BatchPredictionRequest(BaseModel):
    transactions: list[TransactionData]

# Initialize fraud predictor
fraud_predictor = get_fraud_predictor()

@app.post("/api/predict-fraud")
async def predict_fraud(transaction: TransactionData):
    """Predict fraud for a single transaction using ML model"""
    try:
        # Convert transaction data to dict format expected by ML model
        transaction_dict = {
            "transaction_id": transaction.transaction_id,
            "amount": transaction.amount,
            "merchant": transaction.merchant,
            "card_number": transaction.card_number,
            "timestamp": transaction.timestamp,
            "location": transaction.location,
            "customer_id": transaction.customer_id,
            "merchant_category": transaction.merchant_category or transaction.category
        }
        
        # Get ML prediction
        prediction = fraud_predictor.predict(transaction_dict)
        
        # Format response
        return {
            "transaction_id": transaction.transaction_id,
            "is_fraud": prediction['is_fraud'],
            "confidence": prediction['confidence'],
            "fraud_probability": prediction['fraud_probability'],
            "model_used": prediction['model_used'],
            "risk_factors": [
                k for k, v in prediction.get('feature_importance', {}).items() 
                if v > 0.1
            ],
            "explanation": "ML model prediction based on transaction patterns"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict-fraud-batch")
async def predict_fraud_batch(request: BatchPredictionRequest):
    """Predict fraud for multiple transactions"""
    try:
        transactions = []
        for tx in request.transactions:
            transaction_dict = {
                "transaction_id": tx.transaction_id,
                "amount": tx.amount,
                "merchant": tx.merchant,
                "card_number": tx.card_number,
                "timestamp": tx.timestamp,
                "location": tx.location,
                "customer_id": tx.customer_id,
                "merchant_category": tx.merchant_category or tx.category
            }
            transactions.append(transaction_dict)
        
        # Get batch predictions
        predictions = fraud_predictor.batch_predict(transactions)
        
        return {
            "predictions": predictions,
            "count": len(predictions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/model-info")
async def get_model_info():
    """Get information about the current ML model"""
    try:
        return fraud_predictor.get_model_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "model_status": fraud_predictor.get_model_info()['status']}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
