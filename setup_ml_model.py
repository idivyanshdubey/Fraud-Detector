#!/usr/bin/env python3
"""
Quick ML Model Setup Script for Fraud Detection System
Automates the training and verification of the ML fraud detection model
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'sklearn', 'joblib', 'pandas', 'numpy', 'scipy'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("📦 Installing missing packages...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    else:
        print("✅ All dependencies are installed")

def train_model():
    """Train the fraud detection model"""
    print("🧠 Training ML model...")
    
    backend_dir = Path(__file__).parent / "backend"
    train_script = backend_dir / "ml_model" / "train_model.py"
    
    if not train_script.exists():
        print("❌ Training script not found!")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, str(train_script)
        ], cwd=str(backend_dir), capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Model training completed successfully")
            print("📊 Training output:")
            print(result.stdout)
            return True
        else:
            print("❌ Model training failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error training model: {e}")
        return False

def verify_model():
    """Verify the trained model is working"""
    print("🔍 Verifying model...")
    
    backend_dir = Path(__file__).parent / "backend"
    model_file = backend_dir / "ml_model" / "fraud_detection_model.pkl"
    
    if not model_file.exists():
        print("❌ Model file not found!")
        return False
    
    try:
        # Test the model with a sample prediction
        sys.path.insert(0, str(backend_dir))
        from ml_model.fraud_predictor import get_fraud_predictor
        
        predictor = get_fraud_predictor()
        info = predictor.get_model_info()
        
        if info['status'] == 'loaded':
            print("✅ Model loaded successfully")
            print(f"📊 Model type: {info['model_type']}")
            print(f"🔢 Features: {info['n_features']}")
            
            # Test prediction
            test_transaction = {
                "transaction_id": "test_001",
                "amount": 1500.0,
                "merchant": "Test Electronics",
                "card_number": "4532123456789012",
                "timestamp": "2024-01-15T14:30:00Z",
                "location": {"lat": 40.7128, "lng": -74.0060},
                "customer_id": "cust_test",
                "merchant_category": "electronics"
            }
            
            result = predictor.predict(test_transaction)
            print(f"✅ Test prediction: {'FRAUD' if result['is_fraud'] else 'LEGITIMATE'}")
            print(f"🎯 Confidence: {result['confidence']:.2%}")
            print(f"📈 Fraud probability: {result['fraud_probability']:.2%}")
            
            return True
        else:
            print("❌ Model failed to load")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying model: {e}")
        return False

def create_example_requests():
    """Create example API requests for testing"""
    print("📝 Creating example requests...")
    
    examples_dir = Path(__file__).parent / "examples"
    examples_dir.mkdir(exist_ok=True)
    
    # Single transaction example
    single_tx = {
        "transaction_id": "example_001",
        "amount": 2500.0,
        "merchant": "Electronics Store NYC",
        "card_number": "4532-1234-5678-9012",
        "timestamp": "2024-01-15T14:30:00Z",
        "location": {"lat": 40.7128, "lng": -74.0060},
        "customer_id": "cust_12345",
        "category": "electronics"
    }
    
    # Batch transactions example
    batch_tx = {
        "transactions": [
            {
                "transaction_id": "batch_001",
                "amount": 100.0,
                "merchant": "Local Grocery",
                "card_number": "1234-5678-9012-3456",
                "timestamp": "2024-01-15T10:00:00Z",
                "location": {"lat": 40.7589, "lng": -73.9851},
                "customer_id": "cust_001",
                "category": "grocery"
            },
            {
                "transaction_id": "batch_002",
                "amount": 3500.0,
                "merchant": "Luxury Watch Store",
                "card_number": "9876-5432-1098-7654",
                "timestamp": "2024-01-15T02:30:00Z",
                "location": {"lat": 51.5074, "lng": -0.1278},
                "customer_id": "cust_002",
                "category": "luxury"
            }
        ]
    }
    
    with open(examples_dir / "single_transaction.json", "w") as f:
        json.dump(single_tx, f, indent=2)
    
    with open(examples_dir / "batch_transactions.json", "w") as f:
        json.dump(batch_tx, f, indent=2)
    
    print("✅ Example requests created in examples/ directory")

def main():
    """Main setup process"""
    print("🚀 Setting up ML Fraud Detection Model...")
    print("=" * 50)
    
    # Check dependencies
    check_dependencies()
    print()
    
    # Train model
    if train_model():
        print()
        # Verify model
        if verify_model():
            print()
            # Create examples
            create_example_requests()
            print()
            print("🎉 ML Model Setup Complete!")
            print("\nNext steps:")
            print("1. Start the backend: python backend/main.py")
            print("2. Test predictions: curl -X POST http://localhost:8000/api/predict-fraud")
            print("3. Check model info: curl http://localhost:8000/api/model-info")
        else:
            print("❌ Model verification failed")
    else:
        print("❌ Model training failed")

if __name__ == "__main__":
    main()
