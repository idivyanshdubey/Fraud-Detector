"""
FastAPI Backend for Fraud Detection System
Robust production-ready backend with comprehensive monitoring and error handling
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import json
import asyncio
import logging
import os
import signal
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading
import time
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
import uvicorn

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fraud_detection.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_SERVERS', 'localhost:9092').split(',')
    KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'fraud_alerts')
    MAX_ALERTS_BUFFER = int(os.getenv('MAX_ALERTS_BUFFER', '1000'))
    WEBSOCKET_HEARTBEAT_INTERVAL = int(os.getenv('WS_HEARTBEAT', '30'))
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:4200,http://127.0.0.1:4200').split(',')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Pydantic models for API validation
class FraudAlert(BaseModel):
    transaction_id: str
    card_number: str
    merchant: str
    amount: float
    currency: str
    timestamp: str
    fraud_type: str
    fraud_reason: str
    severity: str
    alert_timestamp: str
    location: Optional[Dict[str, Any]] = None

class HealthStatus(BaseModel):
    status: str
    kafka_consumer: str
    active_websocket_connections: int
    alerts_in_buffer: int
    uptime_seconds: float
    memory_usage_mb: float
    timestamp: str

class StatsResponse(BaseModel):
    total_alerts: int
    fraud_types: Dict[str, int]
    severity_distribution: Dict[str, int]
    alerts_last_hour: int
    alerts_last_day: int
    average_alert_rate_per_minute: float
    timestamp: str

# Global state management
class AppState:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.fraud_alerts_buffer: List[Dict[str, Any]] = []
        self.kafka_consumer_thread = None
        self.consumer_running = False
        self.startup_time = datetime.now()
        self.last_kafka_error = None
        self.kafka_reconnect_attempts = 0
        self.max_reconnect_attempts = 5

app_state = AppState()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_metadata[websocket] = {
            "client_id": client_id or str(id(websocket)),
            "connected_at": datetime.now().isoformat(),
            "last_heartbeat": datetime.now()
        }
        logger.info(f"WebSocket connected. Client: {client_id}, Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connection_metadata.pop(websocket, None)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str, exclude: List[WebSocket] = None):
        disconnected = []
        exclude = exclude or []
        
        for connection in self.active_connections:
            if connection in exclude:
                continue
                
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

    def get_connection_info(self) -> List[Dict[str, Any]]:
        return [
            {
                "client_id": metadata["client_id"],
                "connected_at": metadata["connected_at"],
                "duration_seconds": (datetime.now() - datetime.fromisoformat(metadata["connected_at"])).total_seconds()
            }
            for metadata in self.connection_metadata.values()
        ]

manager = ConnectionManager()

def get_memory_usage():
    """Get current memory usage in MB with fallback"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except (ImportError, Exception):
        # Fallback when psutil is not available
        return 0.0

def create_kafka_consumer():
    """Create Kafka consumer with robust configuration"""
    return KafkaConsumer(
        Config.KAFKA_TOPIC,
        bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='fraud_detection_backend',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        session_timeout_ms=30000,
        heartbeat_interval_ms=10000,
        max_poll_records=100,
        max_poll_interval_ms=300000,
        reconnect_backoff_ms=50,
        reconnect_backoff_max_ms=1000
    )

def kafka_consumer_worker():
    """Robust Kafka consumer with error handling and reconnection"""
    global app_state
    
    while app_state.consumer_running and app_state.kafka_reconnect_attempts < app_state.max_reconnect_attempts:
        consumer = None
        try:
            consumer = create_kafka_consumer()
            logger.info(f"Kafka consumer connected to {Config.KAFKA_BOOTSTRAP_SERVERS}")
            app_state.kafka_reconnect_attempts = 0
            app_state.last_kafka_error = None
            
            for message in consumer:
                if not app_state.consumer_running:
                    break
                    
                try:
                    fraud_alert = message.value
                    logger.info(f"Received fraud alert: {fraud_alert.get('transaction_id', 'Unknown')}")
                    
                    # Validate alert structure
                    if not isinstance(fraud_alert, dict):
                        logger.warning("Invalid fraud alert format received")
                        continue
                    
                    # Add to buffer with size limit
                    app_state.fraud_alerts_buffer.append(fraud_alert)
                    if len(app_state.fraud_alerts_buffer) > Config.MAX_ALERTS_BUFFER:
                        app_state.fraud_alerts_buffer.pop(0)
                    
                    # Broadcast to all connected WebSocket clients
                    asyncio.create_task(manager.broadcast(json.dumps({"type": "fraud_alert", "data": fraud_alert})))
                    
                except Exception as e:
                    logger.error(f"Error processing fraud alert: {e}")
                    continue
                    
        except KafkaError as e:
            app_state.last_kafka_error = str(e)
            app_state.kafka_reconnect_attempts += 1
            logger.error(f"Kafka connection error (attempt {app_state.kafka_reconnect_attempts}): {e}")
            
            if app_state.kafka_reconnect_attempts < app_state.max_reconnect_attempts:
                time.sleep(min(2 ** app_state.kafka_reconnect_attempts, 30))  # Exponential backoff
            else:
                logger.error("Max Kafka reconnection attempts reached")
                break
                
        except Exception as e:
            logger.error(f"Unexpected error in Kafka consumer: {e}")
            time.sleep(5)
            
        finally:
            if consumer:
                consumer.close()
                logger.info("Kafka consumer closed")

    logger.info("Kafka consumer worker stopped")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app_state.consumer_running = True
    app_state.kafka_consumer_thread = threading.Thread(target=kafka_consumer_worker, daemon=True)
    app_state.kafka_consumer_thread.start()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        app_state.consumer_running = False
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("FastAPI backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Initiating graceful shutdown...")
    app_state.consumer_running = False
    
    if app_state.kafka_consumer_thread and app_state.kafka_consumer_thread.is_alive():
        app_state.kafka_consumer_thread.join(timeout=10)
    
    logger.info("FastAPI backend shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Fraud Detection API",
    description="Production-ready fraud detection backend with WebSocket and REST endpoints",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with system information"""
    uptime = datetime.now() - app_state.startup_time
    return {
        "message": "Fraud Detection API",
        "version": "1.0.0",
        "status": "running",
        "uptime_seconds": uptime.total_seconds(),
        "kafka_connected": app_state.kafka_reconnect_attempts == 0,
        "active_websocket_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Comprehensive health check endpoint"""
    uptime = datetime.now() - app_state.startup_time
    
    kafka_status = "healthy" if app_state.kafka_reconnect_attempts == 0 else "degraded"
    if app_state.last_kafka_error:
        kafka_status = "error"
    
    return HealthStatus(
        status="healthy" if kafka_status != "error" else "unhealthy",
        kafka_consumer=kafka_status,
        active_websocket_connections=len(manager.active_connections),
        alerts_in_buffer=len(app_state.fraud_alerts_buffer),
        uptime_seconds=uptime.total_seconds(),
        memory_usage_mb=get_memory_usage(),
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/clear-alerts")
async def clear_alerts():
    app_state.fraud_alerts_buffer = []
    return {"status": "cleared"}

@app.get("/api/fraud-alerts", response_model=Dict[str, Any])
async def get_fraud_alerts(limit: int = 50, offset: int = 0):
    """Get fraud alerts with pagination"""
    try:
        if limit > 100:
            limit = 100
        if offset < 0:
            offset = 0
            
        total_alerts = len(app_state.fraud_alerts_buffer)
        start_idx = max(0, total_alerts - offset - limit)
        end_idx = max(0, total_alerts - offset)
        
        recent_alerts = app_state.fraud_alerts_buffer[start_idx:end_idx]
        
        return {
            "alerts": recent_alerts,
            "pagination": {
                "total": total_alerts,
                "limit": limit,
                "offset": offset,
                "returned": len(recent_alerts)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching fraud alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/fraud-alerts/stats", response_model=StatsResponse)
async def get_fraud_stats():
    """Get comprehensive fraud detection statistics"""
    try:
        now = datetime.now()
        
        fraud_types = {}
        severity_distribution = {}
        alerts_last_hour = 0
        alerts_last_day = 0
        
        for alert in app_state.fraud_alerts_buffer:
            fraud_type = alert.get('fraud_type', 'UNKNOWN')
            severity = alert.get('severity', 'UNKNOWN')
            alert_time = datetime.fromisoformat(alert.get('alert_timestamp', now.isoformat()))
            
            fraud_types[fraud_type] = fraud_types.get(fraud_type, 0) + 1
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
            
            if now - alert_time <= timedelta(hours=1):
                alerts_last_hour += 1
            if now - alert_time <= timedelta(days=1):
                alerts_last_day += 1
        
        total_alerts = len(app_state.fraud_alerts_buffer)
        uptime_minutes = (now - app_state.startup_time).total_seconds() / 60
        avg_rate = total_alerts / max(uptime_minutes, 1)
        
        return StatsResponse(
            total_alerts=total_alerts,
            fraud_types=fraud_types,
            severity_distribution=severity_distribution,
            alerts_last_hour=alerts_last_hour,
            alerts_last_day=alerts_last_day,
            average_alert_rate_per_minute=round(avg_rate, 2),
            timestamp=now.isoformat()
        )
    except Exception as e:
        logger.error(f"Error calculating fraud stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/websocket/clients")
async def get_websocket_clients():
    """Get active WebSocket client information"""
    return {
        "active_connections": manager.get_connection_info(),
        "total_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

# Fraud Prediction API Integration
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
    """Fraud prediction endpoint - integrated from fraud_predict_api.py"""
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
        # For now, return a simple prediction based on amount and merchant
        amount = transaction.amount
        merchant = transaction.merchant.lower()
        
        # Robust fraud detection rules
        risk_factors = []
        risk_score = 0
        confidence = 0.15  # default low confidence
        is_fraud = False

        # 1. Amount-based
        if amount > 5000:
            risk_factors.append("Very high transaction amount")
            risk_score += 40
        elif amount > 2000:
            risk_factors.append("High transaction amount")
            risk_score += 25
        elif amount < 100:
            risk_factors.append("Very low transaction amount")
            risk_score -= 10

        # 2. Merchant analysis
        suspicious_keywords = ["test", "fraud", "scam", "bitcoin", "crypto", "gift card"]
        if any(word in merchant for word in suspicious_keywords):
            risk_factors.append("Suspicious merchant name")
            risk_score += 25

        # 3. Card number pattern
        card_number = transaction.card_number.replace('-', '').replace(' ', '')
        if card_number == "" or len(card_number) < 8:
            risk_factors.append("Invalid card number format")
            risk_score += 20
        if card_number.isdigit():
            if len(set(card_number)) == 1:
                risk_factors.append("Card number has all repeating digits")
                risk_score += 20
            if card_number in ["00000000", "12345678", "11111111"]:
                risk_factors.append("Card number is a known invalid pattern")
                risk_score += 20

        # 4. Time-based
        try:
            from dateutil.parser import parse as dtparse
            dt = dtparse(transaction.timestamp)
            if dt.hour < 5 or dt.hour > 23:
                risk_factors.append("Odd transaction hour (late night/early morning)")
                risk_score += 15
        except Exception:
            risk_factors.append("Invalid or missing timestamp")
            risk_score += 10

        # 5. Category-merchant mismatch
        category = (transaction.category or "").lower()
        if (category == "electronics" and "grocery" in merchant) or (category == "grocery" and "electronics" in merchant):
            risk_factors.append("Category and merchant mismatch")
            risk_score += 15

        # 6. Location (mock: flag if lat/lng is 0)
        if transaction.location.get("lat", 0.0) == 0.0 and transaction.location.get("lng", 0.0) == 0.0:
            risk_factors.append("Missing or invalid location")
            risk_score += 10

        # Aggregate
        if risk_score >= 60:
            is_fraud = True
            confidence = 0.9
        elif risk_score >= 40:
            is_fraud = True
            confidence = 0.75
        elif risk_score >= 25:
            is_fraud = True
            confidence = 0.6
        else:
            is_fraud = False
            confidence = 0.15

        reason = ", ".join(risk_factors) if risk_factors else "Normal transaction pattern"

        return {
            "transaction_id": transaction.transaction_id,
            "is_fraud": is_fraud,
            "confidence": confidence,
            "risk_score": min(max(risk_score, 0), 100),
            "reason": reason,
            "explanation": f"Transaction analyzed: ${amount} at {transaction.merchant}",
            "timestamp": datetime.now().isoformat(),
            "spark_job_id": f"mock_job_{transaction.transaction_id}",
            "model_version": "1.0.0-demo"
        }
        
    except Exception as e:
        logger.error(f"Error in fraud prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Fraud prediction failed: {str(e)}")

@app.websocket("/ws/fraud-alerts")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """Enhanced WebSocket endpoint with client identification and heartbeat"""
    await manager.connect(websocket, client_id)
    
    try:
        # Send recent alerts to newly connected client
        if app_state.fraud_alerts_buffer:
            recent_alerts = app_state.fraud_alerts_buffer[-10:]  # Send last 10 alerts
            for alert in recent_alerts:
                await manager.send_personal_message(json.dumps({"type": "fraud_alert", "data": alert}), websocket)
        
        # Send connection confirmation
        await manager.send_personal_message(json.dumps({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }), websocket)
        
        # Keep connection alive and handle client messages
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(), 
                    timeout=Config.WEBSOCKET_HEARTBEAT_INTERVAL
                )
                
                # Handle different message types
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await manager.send_personal_message(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }), websocket)
                    elif message.get("type") == "subscribe":
                        # Handle subscription to specific alert types
                        pass
                except json.JSONDecodeError:
                    # Handle plain text messages
                    await manager.send_personal_message(json.dumps({
                        "type": "echo",
                        "message": data,
                        "timestamp": datetime.now().isoformat()
                    }), websocket)
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await manager.send_personal_message(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
