import React, { useState, useEffect, useRef } from 'react';
import Message from './Message.jsx';
import ChatInput from './ChatInput.jsx';
import ReactMarkdown from 'react-markdown';

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const messagesEndRef = useRef(null);
  const isChatInitialized = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };


  useEffect(() => {
    const initializeChat = async () => {

      if (isChatInitialized.current) {
        return;
      }

      isChatInitialized.current = true;


      // Only run once when session is set and messages history is empty
      // if (currentSessionId && messages.length === 0) {
        setIsTyping(true);
        try {
          const response = await fetch('http://localhost:8001/api/chat/init_session', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ session_id: sessionId }),
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json(); // { response: "..." }
          
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              content: data.response,
              sender: 'assistant',
              timestamp: new Date(),
              type: 'text',
            },
          ]);
        } catch (error) {
          console.error('Error initializing chat:', error);
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              content: 'Sorry, I am unable to connect to the assistant right now.',
              sender: 'assistant',
              timestamp: new Date(),
              type: 'text',
            },
          ]);
        } finally {
          setIsTyping(false);
        }
      };


      if (!sessionId) {
        setSessionId(crypto.randomUUID());
      } else {
        // Once sessionId is set, then attempt to initialize if not already done
        initializeChat();
      }
    }, [sessionId]);


  // Effect to scroll to bottom when messages update
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle sending free-text messages from ChatInput
  const handleSendMessage = async (content) => {
    if (!sessionId) {
      console.error("Session ID not set. Cannot send message.");
      return;
    }

    const userMessage = {
      id: Date.now().toString(),
      content,
      sender: 'patient',
      timestamp: new Date(),
      type: 'text',
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8001/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // Send free-text message. No structured answers needed.
        body: JSON.stringify({ message: content, session_id: sessionId }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json(); // { response: "..." }
      
      // Add assistant's text response
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content: data.response,
          sender: 'assistant',
          timestamp: new Date(),
          type: 'text',
        },
      ]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content: 'Sorry, I am unable to process your request right now.',
          sender: 'assistant',
          timestamp: new Date(),
          type: 'text',
        },
      ]);
    } finally {
      setIsTyping(false);
    }
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