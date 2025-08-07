import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="app-container">
      <nav class="navbar">
        <div class="nav-brand">
          <h1>🛡️ Fraud Detection System</h1>
        </div>
        <div class="nav-links">
          <a routerLink="/dashboard" routerLinkActive="active">Dashboard</a>
          <a routerLink="/upload" routerLinkActive="active">Upload & Check</a>
        </div>
      </nav>
      <main class="main-content">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .navbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 2rem;
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .nav-brand h1 {
      color: white;
      margin: 0;
      font-size: 1.5rem;
    }
    
    .nav-links {
      display: flex;
      gap: 2rem;
    }
    
    .nav-links a {
      color: rgba(255, 255, 255, 0.8);
      text-decoration: none;
      padding: 0.5rem 1rem;
      border-radius: 20px;
      transition: all 0.3s ease;
    }
    
    .nav-links a:hover,
    .nav-links a.active {
      color: white;
      background: rgba(255, 255, 255, 0.2);
    }
    
    .main-content {
      padding: 1rem;
    }
  `]
})
export class AppComponent {
  title = 'Fraud Detection Dashboard';
}
