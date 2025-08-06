"""
PySpark Streaming Job for Real-Time Fraud Detection
Consumes transactions from Kafka, applies fraud rules, outputs alerts
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FraudDetectionJob:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("FraudDetectionStreaming") \
            .config("spark.sql.streaming.checkpointLocation", "./checkpoint") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        
        # Define transaction schema
        self.transaction_schema = StructType([
            StructField("transaction_id", StringType(), True),
            StructField("card_number", StringType(), True),
            StructField("merchant", StringType(), True),
            StructField("amount", DoubleType(), True),
            StructField("currency", StringType(), True),
            StructField("timestamp", StringType(), True),
            StructField("location", StructType([
                StructField("city", StringType(), True),
                StructField("country", StringType(), True),
                StructField("lat", DoubleType(), True),
                StructField("lon", DoubleType(), True)
            ]), True),
            StructField("merchant_category", StringType(), True),
            StructField("card_type", StringType(), True),
            StructField("is_weekend", BooleanType(), True)
        ])
        
        # Fraud detection rules configuration
        self.HIGH_AMOUNT_THRESHOLD = 10000.0
        self.VELOCITY_WINDOW_MINUTES = 5
        self.VELOCITY_THRESHOLD = 3
        
        self.BLACKLISTED_MERCHANTS = ["SuspiciousMerchant", "FraudStore", "ScamShop"]
        self.BLACKLISTED_CARDS = ["4532-0000-0000-0001", "4532-0000-0000-0002"]

    def read_kafka_stream(self):
        """Read streaming data from Kafka topic"""
        return self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "localhost:9092") \
            .option("subscribe", "credit_transactions") \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()

    def parse_transactions(self, kafka_df):
        """Parse JSON messages from Kafka"""
        return kafka_df.select(
            col("key").cast("string").alias("card_key"),
            from_json(col("value").cast("string"), self.transaction_schema).alias("transaction"),
            col("timestamp").alias("kafka_timestamp")
        ).select(
            col("card_key"),
            col("transaction.*"),
            col("kafka_timestamp")
        )

    def apply_fraud_rules(self, transactions_df):
        """Apply fraud detection rules"""
        
        # Add processing timestamp
        enriched_df = transactions_df.withColumn(
            "processing_time", current_timestamp()
        ).withColumn(
            "transaction_timestamp", to_timestamp(col("timestamp"))
        )
        
        # Rule 1: High Amount Detection
        high_amount_fraud = enriched_df.filter(
            col("amount") > self.HIGH_AMOUNT_THRESHOLD
        ).withColumn("fraud_type", lit("HIGH_AMOUNT")) \
         .withColumn("fraud_reason", concat(lit("Transaction amount $"), col("amount"), lit(" exceeds threshold")))
        
        # Rule 2: Blacklist Detection
        blacklist_fraud = enriched_df.filter(
            (col("merchant").isin(self.BLACKLISTED_MERCHANTS)) |
            (col("card_number").isin(self.BLACKLISTED_CARDS))
        ).withColumn("fraud_type", lit("BLACKLIST")) \
         .withColumn("fraud_reason", lit("Merchant or card in blacklist"))
        
        # Rule 3: Velocity Detection (using watermarking for late data)
        velocity_fraud = enriched_df \
            .withWatermark("transaction_timestamp", "10 minutes") \
            .groupBy(
                col("card_number"),
                window(col("transaction_timestamp"), f"{self.VELOCITY_WINDOW_MINUTES} minutes")
            ).agg(
                count("*").alias("transaction_count"),
                collect_list("transaction_id").alias("transaction_ids"),
                max("amount").alias("max_amount"),
                max("merchant").alias("last_merchant"),
                max("processing_time").alias("processing_time"),
                max("timestamp").alias("timestamp"),
                max("location").alias("location")
            ).filter(
                col("transaction_count") >= self.VELOCITY_THRESHOLD
            ).select(
                col("card_number"),
                col("transaction_ids").getItem(0).alias("transaction_id"),
                col("last_merchant").alias("merchant"),
                col("max_amount").alias("amount"),
                lit("USD").alias("currency"),
                col("timestamp"),
                col("location"),
                lit("retail").alias("merchant_category"),
                lit("credit").alias("card_type"),
                lit(False).alias("is_weekend"),
                col("processing_time"),
                lit("VELOCITY").alias("fraud_type"),
                concat(
                    lit("Card used "), col("transaction_count"), 
                    lit(" times in "), lit(self.VELOCITY_WINDOW_MINUTES), lit(" minutes")
                ).alias("fraud_reason")
            )
        
        # Union all fraud types
        all_fraud = high_amount_fraud.unionByName(blacklist_fraud).unionByName(velocity_fraud)
        
        return all_fraud

    def create_fraud_alerts(self, fraud_df):
        """Create structured fraud alerts"""
        return fraud_df.select(
            col("transaction_id"),
            col("card_number"),
            col("merchant"),
            col("amount"),
            col("currency"),
            col("timestamp"),
            col("location"),
            col("fraud_type"),
            col("fraud_reason"),
            col("processing_time"),
            lit("HIGH").alias("severity"),  # Could be enhanced with ML scoring
            current_timestamp().alias("alert_timestamp")
        )

    def write_to_kafka(self, alerts_df):
        """Write fraud alerts to Kafka topic"""
        kafka_output = alerts_df.select(
            col("card_number").alias("key"),
            to_json(struct(
                col("transaction_id"),
                col("card_number"),
                col("merchant"),
                col("amount"),
                col("currency"),
                col("timestamp"),
                col("location"),
                col("fraud_type"),
                col("fraud_reason"),
                col("processing_time"),
                col("severity"),
                col("alert_timestamp")
            )).alias("value")
        )
        
        return kafka_output.writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "localhost:9092") \
            .option("topic", "fraud_alerts") \
            .option("checkpointLocation", "./checkpoint/kafka_output") \
            .outputMode("append") \
            .start()

    def write_to_console(self, alerts_df):
        """Write fraud alerts to console for monitoring"""
        return alerts_df.writeStream \
            .outputMode("append") \
            .format("console") \
            .option("truncate", False) \
            .option("numRows", 20) \
            .trigger(processingTime='10 seconds') \
            .start()

    def run(self):
        """Main execution method"""
        logger.info("Starting Fraud Detection Streaming Job...")
        
        try:
            # Read from Kafka
            kafka_stream = self.read_kafka_stream()
            
            # Parse transactions
            transactions = self.parse_transactions(kafka_stream)
            
            # Apply fraud detection rules
            fraud_transactions = self.apply_fraud_rules(transactions)
            
            # Create fraud alerts
            fraud_alerts = self.create_fraud_alerts(fraud_transactions)
            
            # Start output streams
            kafka_query = self.write_to_kafka(fraud_alerts)
            console_query = self.write_to_console(fraud_alerts)
            
            logger.info("Fraud detection job started successfully")
            logger.info("Monitoring for fraud patterns...")
            
            # Wait for termination
            kafka_query.awaitTermination()
            console_query.awaitTermination()
            
        except Exception as e:
            logger.error(f"Error in fraud detection job: {str(e)}")
            raise
        finally:
            self.spark.stop()

if __name__ == "__main__":
    job = FraudDetectionJob()
    job.run()
