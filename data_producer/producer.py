"""
Credit Card Transaction Data Producer
Generates realistic transaction data and publishes to Kafka topic 'credit_transactions'
"""

import json
import random
import time
from datetime import datetime, timedelta
from kafka import KafkaProducer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionProducer:
    def __init__(self, kafka_servers=['localhost:9092'], topic='credit_transactions'):
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        
        # Sample data for realistic transactions
        self.merchants = [
            "Amazon", "Walmart", "Target", "Starbucks", "McDonald's", "Shell Gas",
            "Best Buy", "Home Depot", "Costco", "CVS Pharmacy", "Uber", "Netflix",
            "Spotify", "Apple Store", "Google Play", "Steam", "PayPal", "Venmo"
        ]
        
        self.cities = [
            "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
            "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
            "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis", "Seattle"
        ]
        
        self.card_numbers = [f"4532-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}" 
                           for _ in range(100)]
        
        # Blacklisted entities for fraud simulation
        self.blacklisted_merchants = ["SuspiciousMerchant", "FraudStore", "ScamShop"]
        self.blacklisted_cards = ["4532-0000-0000-0001", "4532-0000-0000-0002"]

    def generate_transaction(self):
        """Generate a single transaction record"""
        
        # Determine if this should be a fraudulent transaction (10% chance)
        is_fraud = random.random() < 0.1
        
        transaction = {
            "transaction_id": f"txn_{random.randint(100000, 999999)}_{int(time.time())}",
            "card_number": random.choice(self.card_numbers),
            "merchant": random.choice(self.merchants),
            "amount": round(random.uniform(5.0, 500.0), 2),
            "currency": "USD",
            "timestamp": datetime.now().isoformat(),
            "location": {
                "city": random.choice(self.cities),
                "country": "USA",
                "lat": round(random.uniform(25.0, 49.0), 6),
                "lon": round(random.uniform(-125.0, -66.0), 6)
            },
            "merchant_category": random.choice(["retail", "food", "gas", "online", "entertainment"]),
            "card_type": random.choice(["credit", "debit"]),
            "is_weekend": datetime.now().weekday() >= 5
        }
        
        # Inject fraud patterns
        if is_fraud:
            fraud_type = random.choice(["high_amount", "blacklist", "velocity"])
            
            if fraud_type == "high_amount":
                transaction["amount"] = round(random.uniform(10000.0, 50000.0), 2)
            elif fraud_type == "blacklist":
                transaction["merchant"] = random.choice(self.blacklisted_merchants)
                transaction["card_number"] = random.choice(self.blacklisted_cards)
            elif fraud_type == "velocity":
                # Use same card number for velocity fraud
                transaction["card_number"] = self.card_numbers[0]
        
        return transaction

    def start_producing(self, interval=2, max_transactions=None):
        """Start producing transactions at specified interval"""
        logger.info(f"Starting transaction producer - interval: {interval}s")
        
        transaction_count = 0
        
        try:
            while True:
                if max_transactions and transaction_count >= max_transactions:
                    break
                    
                transaction = self.generate_transaction()
                
                # Use card_number as key for partitioning
                key = transaction["card_number"]
                
                self.producer.send(
                    self.topic,
                    key=key,
                    value=transaction
                )
                
                logger.info(f"Sent transaction: {transaction['transaction_id']} - "
                           f"${transaction['amount']} at {transaction['merchant']}")
                
                transaction_count += 1
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Stopping transaction producer...")
        finally:
            self.producer.close()
            logger.info(f"Producer stopped. Total transactions sent: {transaction_count}")

if __name__ == "__main__":
    producer = TransactionProducer()
    
    # Start producing transactions every 2 seconds
    producer.start_producing(interval=2)
