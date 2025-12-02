import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, AlertTriangle } from 'lucide-react';

export default function Message({ message }) {
  const isBot = message.sender === 'assistant';
  const isEmergency = message.type === 'emergency';
  
  return (
    <div className={`message ${isBot ? 'assistant' : 'user'} ${isEmergency ? 'emergency' : ''}`}>
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
        
        <div className={`message-text ${isEmergency ? 'emergency-text' : ''}`}>
          {isEmergency ? (
            // Special rendering for emergency messages if you have them
            <div className="emergency-alert">
              <AlertTriangle size={20} className="emergency-icon" />
              <strong>Emergency Alert:</strong>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          ) : (
            // Standard rendering for text messages
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  );
}