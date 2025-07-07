import React, { useState, useRef, useEffect } from 'react';

export default function ChatInput({ onSendMessage, isLoading }) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
  };

  const handleKeyPress = (e) => {

  };

  return (
    <div className="chat-input-container">
      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="chat-input-field-wrapper">
          <textarea
            ref={textareaRef}
            value={message}
            onKeyPress={handleKeyPress}
            placeholder="Describe your symptoms or ask a health question..."
            className="chat-input-field"
          />
        </div>
        
        <button type="submit" className="chat-send-btn">
        </button>
      </form>
      
      <div className="chat-disclaimer">
        This chatbot provides general health information only. Always consult healthcare professionals for medical advice.
      </div>
    </div>
  );
}