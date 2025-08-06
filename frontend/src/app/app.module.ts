import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppComponent } from './app.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { FraudAlertService } from './services/fraud-alert.service';
import { MaskCardPipe } from './pipes/mask-card.pipe';

@NgModule({
  imports: [
    BrowserModule,
    HttpClientModule,
    FormsModule,
    AppComponent,
    DashboardComponent,
    MaskCardPipe
  ],
  providers: [
    FraudAlertService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
