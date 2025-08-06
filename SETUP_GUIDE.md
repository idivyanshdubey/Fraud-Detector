# 🚨 Real-Time Fraud Detection System - Complete Setup Guide

## System Overview
This system processes credit card transactions in real-time, detects fraudulent activities using configurable rules, and provides a real-time dashboard for monitoring fraud alerts.

## 🎯 Architecture
- **Kafka**: Message broker for transaction ingestion and alert distribution
- **PySpark**: Real-time stream processing for fraud detection
- **FastAPI**: Backend API with WebSocket support for real-time updates
- **Angular**: Modern web dashboard for fraud alert visualization

## 🚀 Quick Start Guide

### Step 1: Prerequisites
```bash
# Check Python version (3.8+ required)
python --version

# Check Node.js version (18+ required)
node --version

# Check Java (for PySpark)
java -version
```

### Step 2: Install Kafka
Download and extract Kafka:
```bash
# Windows (using PowerShell)
# Download from https://kafka.apache.org/downloads
# Extract to C:\kafka

# Start Zookeeper
C:\kafka\bin\windows\zookeeper-server-start.bat C:\kafka\config\zookeeper.properties

# Start Kafka (new terminal)
C:\kafka\bin\windows\kafka-server-start.bat C:\kafka\config\server.properties
```

### Step 3: Create Kafka Topics
```bash
# Create topics
kafka-topics.bat --create --topic credit_transactions --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
kafka-topics.bat --create --topic fraud_alerts --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# Verify topics
kafka-topics.bat --list --bootstrap-server localhost:9092
```

### Step 4: Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install Angular dependencies
cd frontend
npm install
cd ..
```

### Step 5: Start All Components

#### Terminal 1: Data Producer
```bash
cd data_producer
python producer.py
```

#### Terminal 2: PySpark Job
```bash
cd spark_job
python fraud_detection_job.py
```

#### Terminal 3: FastAPI Backend
```bash
cd backend
python main.py
```

#### Terminal 4: Angular Frontend
```bash
cd frontend
npm start
```

## 📊 Dashboard Features

### Real-Time Monitoring
- Live fraud alert updates via WebSocket
- Real-time statistics and metrics
- Connection status indicator

### Alert Management
- Filter by fraud type (HIGH_AMOUNT, BLACKLIST, VELOCITY)
- Filter by severity (HIGH, MEDIUM, LOW)
- Search across merchants, cards, and transactions
- Export alerts to JSON

### Visual Analytics
- Total alerts counter
- Alerts per hour/day metrics
- Fraud type distribution
- Severity breakdown
- Responsive design for mobile/desktop

## 🔧 Configuration Options

### Environment Variables
Create `.env` files for each component:

#### Backend (.env)
```bash
KAFKA_SERVERS=localhost:9092
KAFKA_TOPIC=fraud_alerts
MAX_ALERTS_BUFFER=1000
WS_HEARTBEAT=30
CORS_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
LOG_LEVEL=INFO
```

## 🧪 Testing the System

### 1. Verify All Components
```bash
# Check Kafka topics
kafka-topics.bat --list --bootstrap-server localhost:9092

# Test backend health
curl http://localhost:8000/health

# Test API endpoints
curl http://localhost:8000/api/fraud-alerts
```

### 2. Generate Test Data
The data producer automatically creates fraud patterns:
- **HIGH_AMOUNT**: Transactions > $5000
- **BLACKLIST**: Transactions from blacklisted merchants
- **VELOCITY**: Multiple transactions within 60 seconds

### 3. Monitor Real-Time Updates
- Open http://localhost:4200
- Watch for incoming alerts
- Use browser developer tools to monitor WebSocket connections

## 🐛 Troubleshooting

### Kafka Issues
```bash
# Check if Kafka is running
netstat -an | findstr 9092

# Test Kafka connection
kafka-console-producer.bat --bootstrap-server localhost:9092 --topic test
```

### PySpark Issues
```bash
# Check PySpark installation
python -c "import pyspark; print(pyspark.__version__)"

# Check Java version
java -version
```

### Port Conflicts
- Backend: 8000
- Frontend: 4200
- Kafka: 9092

### Debug Mode
```bash
# Enable debug logging
set LOG_LEVEL=DEBUG
python main.py
```

## 📁 Project Structure
```
Fraud_Detection/
├── README.md
├── requirements.txt
├── data_producer/
│   ├── producer.py
│   └── __init__.py
├── spark_job/
│   ├── fraud_detection_job.py
│   └── __init__.py
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── __init__.py
└── frontend/
    ├── src/app/
    │   ├── components/dashboard/
    │   ├── services/fraud-alert.service.ts
    │   ├── pipes/mask-card.pipe.ts
    │   └── app.module.ts
    ├── proxy.conf.json
    └── package.json
```

## 🎨 Customization

### Adding New Fraud Rules
Edit `spark_job/fraud_detection_job.py`:

```python
def new_fraud_rule(transaction):
    # Custom rule logic
    if transaction['amount'] > 10000 and transaction['location']['country'] != 'US':
        return True, 'INTERNATIONAL_HIGH_AMOUNT', 'High amount international transaction'
    return False, None, None
```

### Customizing Dashboard
- Modify `frontend/src/app/components/dashboard/` for UI changes
- Update `fraud-alert.service.ts` for new data sources
- Customize styling in CSS files

## 📈 Performance Tips

### Kafka Tuning
- Increase partitions: `--partitions 6`
- Monitor consumer lag: `kafka-consumer-groups.bat --describe --group fraud-detector --bootstrap-server localhost:9092`

### PySpark Tuning
- Adjust batch interval: Change `processingTime='10 seconds'`
- Increase memory: `spark-submit --driver-memory 4g fraud_detection_job.py`

## 🚀 Production Deployment

### Using Docker (Future Enhancement)
```bash
# Build and run
docker-compose up --build
```

### Manual Deployment
1. Set up production Kafka cluster
2. Configure environment variables
3. Use process managers (PM2, systemd)
4. Set up reverse proxy (nginx)
5. Enable HTTPS/TLS

## 📞 Support

For issues:
1. Check component logs
2. Verify all services are running
3. Check network connectivity
4. Review configuration files
5. Open GitHub issue with logs
