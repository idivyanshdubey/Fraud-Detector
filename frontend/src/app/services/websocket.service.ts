import { Injectable } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { Observable, Subject } from 'rxjs';
import { FraudAlert } from './fraud-alert.service';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp?: string;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket$: WebSocketSubject<any>;
  private messageSubject = new Subject<WebSocketMessage>();

  constructor() {
    this.socket$ = webSocket('ws://localhost:8000/ws/fraud-alerts');
    
    this.socket$.subscribe({
      next: (message) => this.handleMessage(message),
      error: (error) => console.error('WebSocket error:', error),
      complete: () => console.log('WebSocket connection closed')
    });
  }

  private handleMessage(rawMessage: any) {
    // Handle both formats: raw alert objects and wrapped messages
    let message: WebSocketMessage;
    
    if (rawMessage && typeof rawMessage === 'object' && rawMessage.type) {
      // Already in expected format
      message = rawMessage as WebSocketMessage;
    } else {
      // Raw alert object - wrap it
      message = {
        type: 'new_alert',
        data: rawMessage,
        timestamp: new Date().toISOString()
      };
    }
    
    this.messageSubject.next(message);
  }

  getMessages(): Observable<WebSocketMessage> {
    return this.messageSubject.asObservable();
  }

  getAlerts(): Observable<FraudAlert> {
    return new Observable(observer => {
      this.getMessages().subscribe({
        next: (message) => {
          if (message.type === 'new_alert') {
            observer.next(message.data as FraudAlert);
          }
        },
        error: (error) => observer.error(error),
        complete: () => observer.complete()
      });
    });
  }

  close() {
    this.socket$.complete();
  }
}
