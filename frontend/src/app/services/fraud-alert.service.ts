import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { Observable, BehaviorSubject, Subject, retry, catchError, tap, map } from 'rxjs';
import { HttpClient } from '@angular/common/http';

export interface FraudAlert {
  transaction_id: string;
  card_number: string;
  merchant: string;
  amount: number;
  currency: string;
  timestamp: string;
  fraud_type: string;
  fraud_reason: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  alert_timestamp: string;
  location?: {
    city: string;
    country: string;
    lat: number;
    lon: number;
  };
}

export interface FraudStats {
  total_alerts: number;
  fraud_types: { [key: string]: number };
  severity_distribution: { [key: string]: number };
  alerts_last_hour: number;
  alerts_last_day: number;
  average_alert_rate_per_minute: number;
  timestamp: string;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
}

@Injectable({
  providedIn: 'root'
})
export class FraudAlertService {
  private socket$!: WebSocketSubject<any>;
  private alertsSubject = new BehaviorSubject<FraudAlert[]>([]);
  private statsSubject = new BehaviorSubject<FraudStats | null>(null);
  private connectionStatusSubject = new BehaviorSubject<string>('disconnected');
  
  public alerts$ = this.alertsSubject.asObservable();
  public stats$ = this.statsSubject.asObservable();
  public connectionStatus$ = this.connectionStatusSubject.asObservable();

  private readonly API_BASE_URL = 'http://localhost:8000/api';
  private readonly WS_URL = 'ws://localhost:8000/ws/fraud-alerts';

  constructor(private http: HttpClient, @Inject(PLATFORM_ID) private platformId: Object) {
    if (isPlatformBrowser(this.platformId)) {
      this.connect();
    }
    this.loadInitialData();
  }

  private connect(): void {
    this.socket$ = webSocket({
      url: this.WS_URL,
      deserializer: (msg: MessageEvent) => JSON.parse(msg.data),
      serializer: (msg: any) => JSON.stringify(msg),
      openObserver: {
        next: () => {
          console.log('WebSocket connected');
          this.connectionStatusSubject.next('connected');
        }
      },
      closeObserver: {
        next: () => {
          console.log('WebSocket disconnected');
          this.connectionStatusSubject.next('disconnected');
          this.reconnect();
        }
      }
    });

    this.socket$.pipe(
      retry({ delay: 3000, count: 5 }),
      catchError(error => {
        console.error('WebSocket error:', error);
        this.connectionStatusSubject.next('error');
        return [];
      }),
      tap(message => {
        console.log('[WebSocket] Received message:', message);
        
        if (message.type === 'connection_established') {
          console.log('Connection established:', message);
        } else if (message.type === 'heartbeat') {
          // Handle heartbeat
        } else if (message.type === 'fraud_alert' && message.data) {
          // Handle fraud alert in new format
          this.handleNewAlert(message.data);
        } else if (message.transaction_id) {
          // Handle raw alert object (legacy format)
          this.handleNewAlert(message);
        }
      })
    ).subscribe();
  }

  private reconnect(): void {
    console.log('Attempting to reconnect...');
    setTimeout(() => {
      this.connect();
    }, 5000);
  }

  clearAlerts() {
    return this.http.post(`${this.API_BASE_URL}/clear-alerts`, {});
  }

  resetAlerts() {
    this.alertsSubject.next([]);
    this.updateStats();
  }

  private handleNewAlert(alert: any): void {
    // Defensive: unwrap {data} if present
    let realAlert = alert;
    if (!alert.transaction_id && alert.data) {
      realAlert = alert.data;
    }
    console.log('[FraudAlertService] New alert received:', realAlert);
    
    // Ensure we have a valid alert object
    if (!realAlert || !realAlert.transaction_id) {
      console.warn('[FraudAlertService] Invalid alert received:', realAlert);
      return;
    }
    
    const currentAlerts = this.alertsSubject.value;
    
    // Check for duplicates based on transaction_id
    const existingIndex = currentAlerts.findIndex(a => a.transaction_id === realAlert.transaction_id);
    if (existingIndex !== -1) {
      // Update existing alert instead of adding duplicate
      currentAlerts[existingIndex] = realAlert;
      this.alertsSubject.next([...currentAlerts]);
    } else {
      // Add new alert to the beginning of the array
      const updatedAlerts = [realAlert, ...currentAlerts];
      // Keep only last 100 alerts in memory
      if (updatedAlerts.length > 100) {
        updatedAlerts.splice(100);
      }
      this.alertsSubject.next(updatedAlerts);
    }
    
    this.updateStats();
  }

  private loadInitialData(): void {
    this.loadRecentAlerts();
    this.loadStats();
  }

  private loadRecentAlerts(): void {
    this.http.get<{ alerts: FraudAlert[] }>(`${this.API_BASE_URL}/fraud-alerts`, {
      params: { limit: 50 }
    }).subscribe({
      next: (response) => {
        this.alertsSubject.next(response.alerts);
      },
      error: (error) => {
        console.error('Error loading alerts:', error);
      }
    });
  }

  private loadStats(): void {
    this.http.get<FraudStats>(`${this.API_BASE_URL}/fraud-alerts/stats`).subscribe({
      next: (stats) => {
        this.statsSubject.next(stats);
      },
      error: (error) => {
        console.error('Error loading stats:', error);
      }
    });
  }

  private updateStats(): void {
    this.loadStats();
  }

  getAlerts(): Observable<FraudAlert[]> {
    return this.alerts$;
  }

  getStats(): Observable<FraudStats | null> {
    return this.stats$;
  }

  getConnectionStatus(): Observable<string> {
    return this.connectionStatus$;
  }

  getRecentAlerts(limit: number = 20): Observable<FraudAlert[]> {
    return this.http.get<{ alerts: FraudAlert[] }>(
      `${this.API_BASE_URL}/fraud-alerts`,
      { params: { limit } }
    ).pipe(
      tap(response => {
        this.alertsSubject.next(response.alerts);
      }),
      map((response: any) => response.alerts)
    );
  }

  refreshAlerts(limit: number = 50): Observable<FraudAlert[]> {
    return this.http.get<{ alerts: FraudAlert[] }>(
      `${this.API_BASE_URL}/fraud-alerts`,
      { params: { limit } }
    ).pipe(
      tap(response => {
        console.log('Real-time data fetched:', response.alerts.length, 'alerts');
        this.alertsSubject.next(response.alerts);
      }),
      map((response: any) => response.alerts)
    );
  }

  getFilteredAlerts(filters: {
    fraudType?: string;
    severity?: string;
    merchant?: string;
    dateRange?: { start: string; end: string };
  }): FraudAlert[] {
    let alerts = this.alertsSubject.value;
    
    if (filters.fraudType) {
      alerts = alerts.filter(alert => alert.fraud_type === filters.fraudType);
    }
    
    if (filters.severity) {
      alerts = alerts.filter(alert => alert.severity === filters.severity);
    }
    
    if (filters.merchant) {
      alerts = alerts.filter(alert => 
        alert.merchant.toLowerCase().includes(filters.merchant!.toLowerCase())
      );
    }
    
    if (filters.dateRange) {
      const startDate = new Date(filters.dateRange.start);
      const endDate = new Date(filters.dateRange.end);
      alerts = alerts.filter(alert => {
        const alertDate = new Date(alert.alert_timestamp);
        return alertDate >= startDate && alertDate <= endDate;
      });
    }
    
    return alerts;
  }

  sendPing(): void {
    if (this.socket$ && !this.socket$.closed) {
      this.socket$.next({ type: 'ping' });
    }
  }

  disconnect(): void {
    if (this.socket$ && !this.socket$.closed) {
      this.socket$.complete();
    }
  }
}
