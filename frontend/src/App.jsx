import React, { useState } from 'react';
import Header from './components/Header.jsx';
import Sidebar from './components/Sidebar.jsx';
import ChatInterface from './components/ChatInterface.jsx';
import { Menu, X } from 'lucide-react';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app">
      <div className="app-container">
        <Header />
        
        <div className="main-layout">
          {/* Mobile sidebar overlay */}
          <div className={`mobile-sidebar-overlay ${sidebarOpen ? 'open' : ''}`}>
            <div className="mobile-sidebar-backdrop" onClick={() => setSidebarOpen(false)} />
            <div className="mobile-sidebar-panel">
              <div className="mobile-sidebar-header">
                <h2 className="mobile-sidebar-title">Menu</h2>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="mobile-close-btn"
                >
                  <X size={20} />
                </button>
              </div>
              <Sidebar />
            </div>
          </div>

          {/* Desktop sidebar */}
          <div className="sidebar-desktop">
            <Sidebar />
          </div>

          {/* Main chat area */}
          <div className="chat-area">
            {/* Mobile menu button */}
            <div className="mobile-header">
              <button
                onClick={() => setSidebarOpen(true)}
                className="mobile-menu-btn"
              >
                <Menu size={20} />
              </button>
              <span className="mobile-header-title">Medical Chat Assistant</span>
            </div>

            <ChatInterface />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;