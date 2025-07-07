import React from 'react';
import { Activity, Shield } from 'lucide-react';

export default function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-brand">
          <div className="header-logo">
            <Activity size={24} />
          </div>
          <div>
            <h1 className="header-title">HealthTalk</h1>
            <p className="header-subtitle">AI Medical Companion</p>
          </div>
        </div>
        
        <div className="header-badge">
          <Shield size={16} />
          <span className="header-badge-text">HIPAA Compliant</span>
        </div>
      </div>
    </header>
  );
}