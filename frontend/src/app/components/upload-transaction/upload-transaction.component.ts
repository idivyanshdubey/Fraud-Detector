import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ToastService } from '../../services/toast.service';

interface TransactionData {
  transaction_id: string;
  amount: number;
  merchant: string;
  card_number: string;
  timestamp: string;
  location: { lat: number; lng: number };
  customer_id: string;
  category?: string;
}

interface FraudPrediction {
  transaction_id: string;
  is_fraud: boolean;
  confidence: number;
  risk_score: number;
  explanation: string;
  reason: string;
  timestamp: string;
}

@Component({
  selector: 'app-upload-transaction',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './upload-transaction.component.html',
  styleUrls: ['./upload-transaction.component.css']
})
export class UploadTransactionComponent {
  uploadedFile: File | null = null;
  isProcessing = false;
  prediction: FraudPrediction | null = null;
  sampleData: TransactionData = {
    transaction_id: 'TXN' + Date.now(),
    amount: 1250.50,
    merchant: 'Amazon',
    card_number: '4532-1234-5678-9012',
    timestamp: new Date().toISOString(),
    location: { lat: 40.7128, lng: -74.0060 },
    customer_id: 'CUST123',
    category: 'online_purchase'
  };

  constructor(
    private http: HttpClient,
    private toastService: ToastService,
    private cdr: ChangeDetectorRef
  ) {}

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.uploadedFile = input.files[0];
      console.log('File selected:', this.uploadedFile.name, this.uploadedFile.type, this.uploadedFile.size);
      this.readFile();
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    if (event.dataTransfer?.files[0]) {
      this.uploadedFile = event.dataTransfer.files[0];
      this.readFile();
    }
  }

  private readFile() {
    if (!this.uploadedFile) {
      console.log('No file to read');
      return;
    }
    
    console.log('Reading file:', this.uploadedFile.name);
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        console.log('File content:', content.substring(0, 200) + '...');
        const data = JSON.parse(content);
        console.log('Parsed JSON:', data);
        
        // Ensure required fields are present
        const requiredFields = ['transaction_id', 'amount', 'merchant', 'card_number', 'customer_id'];
        const missingFields = requiredFields.filter(field => !data[field]);
        
        if (missingFields.length > 0) {
          this.toastService.error(`Missing required fields: ${missingFields.join(', ')}`);
          return;
        }
        
        this.sampleData = { 
          ...this.sampleData, 
          ...data,
          location: data.location || this.sampleData.location,
          timestamp: data.timestamp || new Date().toISOString()
        };
        this.toastService.success('File loaded successfully');
      } catch (error) {
        console.error('Error parsing file:', error);
        this.toastService.error(`Invalid JSON format: ${error}`);
      }
    };
    
    reader.onerror = (error) => {
      console.error('File reading error:', error);
      this.toastService.error('Failed to read file');
    };
    
    reader.readAsText(this.uploadedFile);
  }

  predictFraud() {
    // Validate data before sending
    const validationErrors = this.validateTransactionData(this.sampleData);
    if (validationErrors.length > 0) {
      this.toastService.error(`Validation failed: ${validationErrors.join(', ')}`);
      return;
    }

    this.isProcessing = true;
    this.prediction = null;

    const payload = {
      transaction_id: this.sampleData.transaction_id,
      amount: Number(this.sampleData.amount),
      merchant: String(this.sampleData.merchant),
      card_number: String(this.sampleData.card_number),
      timestamp: String(this.sampleData.timestamp),
      location: {
        lat: Number(this.sampleData.location?.lat || 0),
        lng: Number(this.sampleData.location?.lng || 0)
      },
      customer_id: String(this.sampleData.customer_id),
      category: String(this.sampleData.category || 'unknown')
    };

    this.http.post<FraudPrediction>('http://localhost:8000/api/predict-fraud', payload)
      .subscribe({
        next: (result) => {
          this.prediction = result;
          this.isProcessing = false;
          this.cdr.detectChanges();
          
          if (result.is_fraud) {
            this.toastService.error(`🚨 Fraud detected! Risk: ${result.risk_score.toFixed(1)}%`);
          } else {
            this.toastService.success(`✅ Transaction is safe. Confidence: ${(result.confidence * 100).toFixed(1)}%`);
          }
        },
        error: (error) => {
          this.isProcessing = false;
          
          let errorMsg = 'Unknown error occurred';
          if (error.status === 0) {
            errorMsg = 'Cannot connect to server. Please ensure backend is running on port 8000';
          } else if (error.status >= 400) {
            errorMsg = `Server error: ${error.status} - ${error.error?.detail || error.message}`;
          } else {
            errorMsg = `Error: ${error.message}`;
          }
          
          this.toastService.error(`❌ ${errorMsg}`);
        }
      });
  }

  private validateTransactionData(data: any): string[] {
    const errors: string[] = [];
    
    if (!data.transaction_id || typeof data.transaction_id !== 'string') {
      errors.push('transaction_id is required and must be a string');
    }
    
    if (!data.amount || isNaN(Number(data.amount))) {
      errors.push('amount is required and must be a number');
    }
    
    if (!data.merchant || typeof data.merchant !== 'string') {
      errors.push('merchant is required and must be a string');
    }
    
    if (!data.card_number || typeof data.card_number !== 'string') {
      errors.push('card_number is required and must be a string');
    }
    
    if (!data.customer_id || typeof data.customer_id !== 'string') {
      errors.push('customer_id is required and must be a string');
    }
    
    if (!data.timestamp || typeof data.timestamp !== 'string') {
      errors.push('timestamp is required and must be a string');
    }
    
    if (!data.location || typeof data.location !== 'object') {
      errors.push('location is required and must be an object');
    }
    
    return errors;
  }

  useSampleData() {
    this.sampleData = {
      transaction_id: 'TXN' + Date.now(),
      amount: Math.round(Math.random() * 5000 + 100),
      merchant: ['Amazon', 'Walmart', 'Target', 'Best Buy'][Math.floor(Math.random() * 4)],
      card_number: '4532-1234-5678-9012',
      timestamp: new Date().toISOString(),
      location: { 
        lat: 40.7128 + (Math.random() - 0.5) * 2, 
        lng: -74.0060 + (Math.random() - 0.5) * 2 
      },
      customer_id: 'CUST' + Math.floor(Math.random() * 1000),
      category: 'online_purchase'
    };
    this.prediction = null;
  }

  resetForm() {
    this.uploadedFile = null;
    this.prediction = null;
    this.useSampleData();
  }
}
