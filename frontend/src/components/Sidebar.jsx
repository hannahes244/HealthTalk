import React from 'react';
import { Heart, Shield, Clock, AlertCircle } from 'lucide-react';

export default function Sidebar() {
  const quickActions = [
    {
      icon: Heart,
      title: 'Symptom Checker',
      description: 'Get guidance on common symptoms',
      colorClass: 'red'
    },
    {
      icon: Shield,
      title: 'Health Tips',
      description: 'Daily wellness advice',
      colorClass: 'green'
    },
    {
      icon: Clock,
      title: 'Medication Reminders',
      description: 'Never miss a dose',
      colorClass: 'blue'
    },
    {
      icon: AlertCircle,
      title: 'Emergency Info',
      description: 'Know when to seek help',
      colorClass: 'orange'
    }
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2 className="sidebar-title">Quick Actions</h2>
        <p className="sidebar-description">Common health topics and tools</p>
      </div>
      
      <div className="sidebar-content">
        {quickActions.map((action, index) => (
          <button key={index} className="quick-action">
            <div className="quick-action-content">
              <div className={`quick-action-icon ${action.colorClass}`}>
                <action.icon size={20} />
              </div>
              <div className="quick-action-text">
                <h3 className="quick-action-title">{action.title}</h3>
                <p className="quick-action-desc">{action.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
      
      <div className="sidebar-footer">
        <div className="notice-card">
          <div className="notice-header">
            <Shield size={16} />
            Important Notice
          </div>
          <p className="notice-text">
            This AI provides general health information only. For medical emergencies, call 911 immediately.
          </p>
        </div>
      </div>
    </div>
  );
}