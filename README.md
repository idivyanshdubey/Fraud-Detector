# Real-Time Fraud Detection System

A comprehensive fraud detection system using **Machine Learning**, Kafka, PySpark, FastAPI, and Angular for real-time transaction monitoring and intelligent fraud detection.

## 🚀 What's New - ML Model Integration

**Version 2.0** introduces advanced machine learning capabilities:
- **Random Forest Classifier** for fraud prediction with 95%+ accuracy
- **Real-time ML inference** via REST API
- **Feature importance analysis** for explainable AI
- **Fallback rule-based detection** for reliability
- **Batch prediction support** for high-throughput scenarios

## Architecture Overview

```
Credit Transactions → Kafka → PySpark Streaming → ML Model → Fraud Alerts → FastAPI → WebSocket → Angular Dashboard
                     ↓
              Real-time ML Inference API
```

## 🧠 ML Model Features

### Model Capabilities
- **Algorithm**: Random Forest Classifier with hyperparameter tuning
- **Features**: 10+ engineered features including amount patterns, merchant risk, location analysis, temporal patterns
- **Accuracy**: >95% on synthetic test data
- **Latency**: <100ms per prediction
- **Explainability**: Feature importance scores for each prediction

### Key Features Analyzed
- Transaction amount patterns
- Merchant category risk scoring
- Geographic location anomalies
- Time-based transaction patterns
- Card age and usage history
- Transaction frequency analysis

## Components

### 1. Data Producer (`data_producer/`)
- Generates sample credit card transactions with realistic patterns
- Publishes to Kafka topic `credit_transactions`
- Configurable transaction volume and fraud rate

### 2. PySpark Streaming Job (`spark_job/`)
- Consumes transactions from Kafka
- **Enhanced**: Can integrate with ML model for real-time scoring
- Publishes alerts to `fraud_alerts` topic
- Configurable fraud detection rules

### 3. FastAPI Backend (`backend/`)
- **NEW**: ML Model Integration (`ml_model/`)
  - `fraud_predictor.py`: Core ML prediction service
  - `train_model.py`: Model training and evaluation pipeline
- Consumes fraud alerts from Kafka
- WebSocket endpoint for real-time updates
- REST API for historical data and ML predictions

### 4. Angular Frontend (`frontend/`)
- Real-time dashboard with ML insights
- WebSocket integration for live updates
- Fraud alert visualization with confidence scores
- Model performance metrics display

### 5. ML Model Service (`backend/ml_model/`)
- **Model Training**: `train_model.py`
- **Prediction Service**: `fraud_predictor.py`
- **Model Persistence**: Joblib for model serialization
- **Feature Engineering**: Real-time feature extraction from transactions

## Prerequisites

- Python 3.8+
- Apache Kafka (running on localhost:9092)
- Node.js 18+
- Angular CLI
- Java 8+ (for Spark)

## Quick Start

1. **Start Kafka Server** (handle manually as specified)
2. **Create Kafka Topics**:
   ```bash
   kafka-topics.sh --create --topic credit_transactions --bootstrap-server localhost:9092
   kafka-topics.sh --create --topic fraud_alerts --bootstrap-server localhost:9092
   ```

3. **Setup Python Environment**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Data Producer**:
   ```bash
   python data_producer/producer.py
   ```

5. **Start PySpark Job**:
   ```bash
   spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0 spark_job/fraud_detection_job.py
   ```

6. **Start FastAPI Backend**:
   ```bash
   cd backend && uvicorn main:app --reload
   ```

7. **Start Angular Frontend**:
   ```bash
   cd frontend && ng serve
   ```

## Fraud Detection Rules

- **High Amount**: Transactions > $10,000
- **Velocity Check**: Multiple transactions from same card within short time
- **Blacklist**: Known fraudulent merchant/card patterns
- **Geographic Anomaly**: Transactions from unusual locations

## Tech Stack

- **Streaming**: Apache Kafka, PySpark Structured Streaming
- **Backend**: FastAPI, WebSocket, asyncio
- **Frontend**: Angular 20+, WebSocket, Bootstrap/Material
- **Data**: JSON, Kafka Connect

## 🧪 ML Model Setup

### 1. Train the Fraud Detection Model
```bash
cd backend
python ml_model/train_model.py
```

This will:
- Generate 10,000 synthetic training samples
- Train a Random Forest classifier with hyperparameter tuning
- Evaluate model performance (expect >95% accuracy)
- Save the trained model as `fraud_detection_model.pkl`

### 2. Verify ML Model Installation
```bash
python -c "from ml_model.fraud_predictor import get_fraud_predictor; print('ML Model loaded:', get_fraud_predictor().get_model_info())"
```

### 3. Test ML Predictions
```bash
# Test single transaction prediction
curl -X POST http://localhost:8000/api/predict-fraud \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "test_123",
    "amount": 2500.0,
    "merchant": "High Risk Electronics",
    "card_number": "4532-1234-5678-9012",
    "timestamp": "2024-01-15T14:30:00Z",
    "location": {"lat": 40.7128, "lng": -74.0060},
    "customer_id": "cust_456",
    "category": "electronics"
  }'

# Test batch prediction
curl -X POST http://localhost:8001/api/predict-fraud-batch \
  -H "Content-Type: application/json" \
  -d '{"transactions": [{"transaction_id": "batch_1", "amount": 100, "merchant": "Grocery Store", "card_number": "1234", "timestamp": "2024-01-15T14:30:00Z", "location": {"lat": 0, "lng": 0}, "customer_id": "cust_1", "category": "grocery"}]}'
```

## 🎯 API Endpoints

### Core Fraud Detection
- `GET /` - System information with ML model status
- `GET /health` - Health check with Kafka and ML model status
- `GET /api/fraud-alerts` - Get fraud alerts (paginated)
- `POST /api/predict-fraud` - ML-based fraud prediction
- `GET /api/fraud-stats` - Get fraud statistics with ML insights
- `GET /api/websocket-clients` - Active WebSocket clients
- `DELETE /api/clear-alerts` - Clear alert buffer

### ML Model APIs
- `POST /api/predict-fraud` - Single transaction prediction
- `POST /api/predict-fraud-batch` - Batch transaction predictions
- `GET /api/model-info` - ML model information and features

### WebSocket
- `ws://localhost:8000/ws` - Real-time fraud alerts with ML confidence
- `ws://localhost:8000/ws/{client_id}` - WebSocket with client ID

## 🔧 Configuration

### Environment Variables
- `KAFKA_SERVERS` - Kafka bootstrap servers (default: localhost:9092)
- `KAFKA_TOPIC` - Kafka topic for alerts (default: fraud_alerts)
- `MAX_ALERTS_BUFFER` - Max alerts to keep in memory (default: 1000)
- `WS_HEARTBEAT` - WebSocket heartbeat interval (default: 30)
- `CORS_ORIGINS` - Allowed CORS origins
- `LOG_LEVEL` - Logging level (default: INFO)

### ML Model Configuration
- Model file: `backend/ml_model/fraud_detection_model.pkl`
- Feature list: 10+ engineered features
- Prediction threshold: 0.5 (configurable)
- Fallback: Rule-based detection if ML fails

## 📊 Model Performance

### Expected Metrics (on synthetic data)
- **Accuracy**: 95-97%
- **Precision**: 94-96%
- **Recall**: 92-95%
- **F1-Score**: 93-95%
- **ROC-AUC**: 0.98+
- **Prediction Latency**: <100ms

### Feature Importance
1. Transaction amount
2. Transaction frequency (24h)
3. Merchant risk score
4. Location risk score
5. Time-based patterns
6. Card age and usage history

## 🔍 Monitoring & Debugging

### Logs
- Application logs: `backend/fraud_detection.log`
- ML model logs: Console output during training
- Kafka logs: Check Kafka server logs

### Health Checks
```bash
# Check ML model health
curl http://localhost:8000/api/model-info

# Check system health
curl http://localhost:8000/health

# Check ML prediction API health
curl http://localhost:8001/health
```

## 🛠️ Development

### Adding New Features
1. Update feature engineering in `ml_model/fraud_predictor.py`
2. Retrain model with `python ml_model/train_model.py`
3. Update API endpoints if needed
4. Test with sample predictions

### Custom Model Training
```python
from backend.ml_model.train_model import FraudModelTrainer

trainer = FraudModelTrainer()
trainer.run_training_pipeline()
```

## 📈 Production Deployment

### Docker Support
```bash
# Build and run with Docker (coming soon)
docker-compose up
```

### Scaling
- Horizontal scaling with multiple ML API instances
- Load balancing with nginx
- Kafka partitioning for high throughput
- Redis caching for model predictions

---

*Built for real-time fraud detection and monitoring*
