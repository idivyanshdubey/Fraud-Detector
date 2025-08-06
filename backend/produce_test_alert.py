from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

alert = {
    "transaction_id": "TX123456",
    "card_number": "4111111111111111",
    "merchant": "Test Merchant",
    "amount": 121.45,
    "currency": "USD",
    "timestamp": "2025-08-06T12:45:00",
    "fraud_type": "Test Fraud",
    "fraud_reason": "Testing",
    "severity": "high",
    "alert_timestamp": "2025-08-06T12:45:00",
    "location": {"city": "Test City"}
}

producer.send('fraud_alerts', {
    "type": "fraud_alert",
    "data": alert
})
producer.flush()
print("Test alert produced!")
