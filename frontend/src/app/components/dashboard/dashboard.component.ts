import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule, AsyncPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MaskCardPipe } from '../../pipes/mask-card.pipe';
import { Observable, Subscription, interval } from 'rxjs';
import { FraudAlertService, FraudAlert, FraudStats } from '../../services/fraud-alert.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, AsyncPipe, MaskCardPipe, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class DashboardComponent implements OnInit, OnDestroy {
  // Used for *ngFor trackBy
  public trackByTransactionId(index: number, alert: FraudAlert): string {
    return alert.transaction_id;
  }
  alerts$: Observable<FraudAlert[]>;
  stats$: Observable<FraudStats | null>;
  connectionStatus$: Observable<string>;
  
  filteredAlerts: FraudAlert[] = [];
  searchTerm: string = '';
  selectedFraudType: string = 'ALL';
  selectedSeverity: string = 'ALL';
  private _allAlerts: FraudAlert[] = [];
  
  private subscription = new Subscription();
  private autoRefresh = true;

  constructor(
    private fraudAlertService: FraudAlertService,
    private cdr: ChangeDetectorRef
  ) {
    this.alerts$ = this.fraudAlertService.getAlerts();
    this.stats$ = this.fraudAlertService.getStats();
    this.connectionStatus$ = this.fraudAlertService.getConnectionStatus();
  }

  clearAlerts(): void {
    console.log('Clear Alerts button clicked');
    this.fraudAlertService.clearAlerts().subscribe({
      next: () => {
        this.filteredAlerts = [];
        this.fraudAlertService.resetAlerts();
        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error('Error clearing alerts:', error);
        this.cdr.markForCheck();
      }
    });
  }

  ngOnInit(): void {
    this.subscription.add(
      this.alerts$.subscribe(alerts => {
        // Always store the original alerts
        this._allAlerts = alerts;
        this.applyFilters();
        this.cdr.markForCheck();
      })
    );

    // Auto-refresh stats every 30 seconds
    if (this.autoRefresh) {
      this.subscription.add(
        interval(30000).subscribe(() => {
          this.fraudAlertService.getStats().subscribe();
        })
      );
    }
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  applyFilters(): void {
    let alerts = [...this._allAlerts];
    // Search filter
    if (this.searchTerm && this.searchTerm.trim().length > 0) {
      const term = this.searchTerm.toLowerCase();
      alerts = alerts.filter(alert =>
        (alert.merchant && alert.merchant.toLowerCase().includes(term)) ||
        (alert.card_number && alert.card_number.toLowerCase().includes(term)) ||
        (alert.transaction_id && alert.transaction_id.toLowerCase().includes(term)) ||
        (alert.fraud_reason && alert.fraud_reason.toLowerCase().includes(term))
      );
    }
    // Fraud type filter
    if (this.selectedFraudType && this.selectedFraudType !== 'ALL') {
      alerts = alerts.filter(alert => alert.fraud_type === this.selectedFraudType);
    }
    // Severity filter
    if (this.selectedSeverity && this.selectedSeverity !== 'ALL') {
      alerts = alerts.filter(alert => alert.severity === this.selectedSeverity);
    }
    this.filteredAlerts = alerts;
  }

  onSearchChange(): void {
    this.applyFilters();
  }

  onFraudTypeChange(type: string): void {
    this.selectedFraudType = type;
    this.applyFilters();
  }

  onSeverityChange(severity: string): void {
    this.selectedSeverity = severity;
    this.applyFilters();
  }

  clearFilters(): void {
    console.log('Clear Filters button clicked');
    this.searchTerm = '';
    this.selectedFraudType = 'ALL';
    this.selectedSeverity = 'ALL';
    this.applyFilters();
    this.cdr.markForCheck();
  }

  getSeverityClass(severity: string): string {
    switch (severity) {
      case 'HIGH': return 'severity-high';
      case 'MEDIUM': return 'severity-medium';
      case 'LOW': return 'severity-low';
      default: return 'severity-unknown';
    }
  }

  getFraudTypeIcon(fraudType: string): string {
    switch (fraudType) {
      case 'HIGH_AMOUNT': return '💰';
      case 'BLACKLIST': return '🚫';
      case 'VELOCITY': return '⚡';
      default: return '⚠️';
    }
  }

  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }

  getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  }

  getConnectionStatusClass(status: string): string {
    switch (status) {
      case 'connected': return 'status-connected';
      case 'disconnected': return 'status-disconnected';
      case 'error': return 'status-error';
      default: return 'status-unknown';
    }
  }

  getConnectionStatusIcon(status: string): string {
    switch (status) {
      case 'connected': return '🟢';
      case 'disconnected': return '🔴';
      case 'error': return '🟡';
      default: return '⚪';
    }
  }

  refreshData(): void {
    console.log('Refresh button clicked');
    this.fraudAlertService.getRecentAlerts(50).subscribe({
      next: (refreshedAlerts) => {
        this._allAlerts = refreshedAlerts;
        this.applyFilters();
        this.cdr.markForCheck();
        console.log('Data refreshed successfully');
      },
      error: (error) => {
        console.error('Error refreshing data:', error);
        this.cdr.markForCheck();
      }
    });
  }

  getFraudTypeOptions(): string[] {
    return ['ALL', 'HIGH_AMOUNT', 'BLACKLIST', 'VELOCITY'];
  }

  getSeverityOptions(): string[] {
    return ['ALL', 'HIGH', 'MEDIUM', 'LOW'];
  }

  exportAlerts(): void {
    console.log('Export button clicked');
    if (this.filteredAlerts.length === 0) {
      console.warn('No alerts to export.');
      return;
    }
    const dataStr = JSON.stringify(this.filteredAlerts, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `fraud_alerts_${new Date().toISOString()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    this.cdr.markForCheck();
  }
}
