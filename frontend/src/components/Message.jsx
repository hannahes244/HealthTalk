import React from 'react';
import { Bot, User, AlertTriangle } from 'lucide-react';

export default function Message({ message }) {
  const isBot = message.sender === 'assistant';
  const isEmergency = message.type === 'emergency';
  
  return (
    <div className={`message ${isBot ? 'assistant' : 'user'}`}>
      <div className={`message-avatar ${isBot ? 'bot' : 'user'}`}>
        {isBot ? <Bot size={16}/> : <User size={16}/>}
      </div>
      
      <div className="message-content">
        <div className="message-header">
          <span className="message-sender">
            {isBot ? 'HeathTalk' : 'You'}
          </span>
          <span className="message-time">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        
        <div className={`message-text`}>
          {message.content}
        </div>
      </div>
    </div>
  );
}