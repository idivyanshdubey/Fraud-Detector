import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

export interface ToastMessage {
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private toastSubject = new Subject<ToastMessage>();
  toast$ = this.toastSubject.asObservable();

  show(message: string, type: ToastMessage['type'] = 'info', duration: number = 3000) {
    this.toastSubject.next({ message, type, duration: duration || 3000 });
  }

  success(message: string, duration?: number) {
    this.show(message, 'success', duration || 3000);
  }

  error(message: string, duration?: number) {
    this.show(message, 'error', duration || 3000);
  }

  warning(message: string, duration?: number) {
    this.show(message, 'warning', duration || 3000);
  }

  info(message: string, duration?: number) {
    this.show(message, 'info', duration || 3000);
  }
}
