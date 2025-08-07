import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil } from 'rxjs';
import { ToastService, ToastMessage } from '../../services/toast.service';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="toast-container" *ngIf="currentToast">
      <div class="toast-message" [class]="'toast-' + currentToast.type">
        <div class="toast-content">
          <span class="toast-icon">{{ getIcon(currentToast.type) }}</span>
          <span class="toast-text">{{ currentToast.message }}</span>
          <button class="toast-close" (click)="dismiss()">&times;</button>
        </div>
        <div class="toast-progress" *ngIf="currentToast.duration">
          <div class="toast-progress-bar" [style.animation-duration]="currentToast.duration + 'ms'"></div>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./toast.component.css']
})
export class ToastComponent implements OnInit, OnDestroy {
  currentToast: ToastMessage | null = null;
  private destroy$ = new Subject<void>();

  constructor(private toastService: ToastService) {}

  ngOnInit() {
    this.toastService.toast$
      .pipe(takeUntil(this.destroy$))
      .subscribe(toast => {
        this.showToast(toast);
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  showToast(toast: ToastMessage) {
    this.currentToast = toast;
    
    if (toast.duration) {
      setTimeout(() => {
        this.dismiss();
      }, toast.duration);
    }
  }

  dismiss() {
    this.currentToast = null;
  }

  getIcon(type: string): string {
    switch (type) {
      case 'success': return '✓';
      case 'error': return '✗';
      case 'warning': return '⚠';
      case 'info': return 'ℹ';
      default: return 'ℹ';
    }
  }
}
