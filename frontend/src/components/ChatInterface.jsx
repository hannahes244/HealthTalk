import React, { useState, useEffect, useRef } from 'react';
import Message from './Message.jsx';
import ChatInput from './ChatInput.jsx';

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);


  useEffect(() => {
    // Welcome message
    const welcomeMessage = {
      id: '1',
      content: "Hello! I'm HealthTalk, your AI medical companion. I can help you understand symptoms, provide general health guidance, and determine when you should seek professional medical care.\n\nPlease remember that I provide general information only and cannot replace professional medical advice. For emergencies, always call 911 immediately.\n\nHow can I help you today?",
      sender: 'assistant',
      timestamp: new Date(),
      type: 'text'
    };
    setMessages([welcomeMessage]);
  }, []);

  const handleSendMessage = async (content) => {
    const userMessage = {
      id: Date.now().toString(),
      content,
      sender: 'patient',
      timestamp: new Date(),
      type: 'text'
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);
    
  };

  return (
    <div className="chat-interface">
      <div className="messages-container">
        <div className="messages-wrapper">
          {messages.map((message) => (
            <Message key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      <ChatInput onSendMessage={handleSendMessage} isLoading={isTyping} />
    </div>
  );
}