from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import requests
import json

app = FastAPI()

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

@app.post("/api/predict-fraud")
async def predict_fraud(transaction: TransactionData):
    try:
        # Convert to Spark job format
        spark_payload = {
            "transaction_id": transaction.transaction_id,
            "amount": transaction.amount,
            "merchant": transaction.merchant,
            "card_number": transaction.card_number,
            "timestamp": transaction.timestamp,
            "latitude": transaction.location.get("lat", 0.0),
            "longitude": transaction.location.get("lng", 0.0),
            "customer_id": transaction.customer_id,
            "category": transaction.category
        }
        
        # Mock Spark prediction (replace with actual Spark API call)
        # For now, return a simple prediction based on amount
        is_fraud = transaction.amount > 1000  # Simple rule for demo
        confidence = 0.85 if is_fraud else 0.15
        
        return {
            "transaction_id": transaction.transaction_id,
            "is_fraud": is_fraud,
            "confidence": confidence,
            "risk_score": confidence * 100,
            "explanation": f"Transaction amount ${transaction.amount} {'exceeds' if is_fraud else 'within'} normal range",
            "timestamp": transaction.timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
