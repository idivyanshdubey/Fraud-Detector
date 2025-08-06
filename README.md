# Real-Time Fraud Detection System

A comprehensive fraud detection system using Kafka, PySpark, FastAPI, and Angular for real-time transaction monitoring and alerting.

## Architecture Overview

```
Credit Transactions → Kafka → PySpark Streaming → Fraud Alerts → FastAPI → WebSocket → Angular Dashboard
```

## Components

### 1. Data Producer (`data_producer/`)
- Generates sample credit card transactions
- Publishes to Kafka topic `credit_transactions`

### 2. PySpark Streaming Job (`spark_job/`)
- Consumes transactions from Kafka
- Applies fraud detection rules
- Publishes alerts to `fraud_alerts` topic

### 3. FastAPI Backend (`backend/`)
- Consumes fraud alerts from Kafka
- WebSocket endpoint for real-time updates
- REST API for historical data

### 4. Angular Frontend (`frontend/`)
- Real-time dashboard
- WebSocket integration
- Fraud alert visualization

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

---

*Built for real-time fraud detection and monitoring*
