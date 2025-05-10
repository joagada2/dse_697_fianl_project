import React, { useEffect, useState, useRef } from 'react';
import './ChatApp.css';
import ReactMarkdown from 'react-markdown';
import { FaRegCopy } from 'react-icons/fa';

const API_URL = 'http://3.143.23.19:8000/docs';
const SESSION_KEY = 'chat_session_id';

function ChatApp() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('chat_messages');
    return saved ? JSON.parse(saved) : [];
  });
  const chatBoxRef = useRef(null);
  const [sessionId, setSessionId] = useState(() => {
    const saved = localStorage.getItem(SESSION_KEY);
    if (saved) return saved;
    const newId = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, newId);
    return newId;
  });

  useEffect(() => {
    localStorage.setItem('chat_messages', JSON.stringify(messages));
    chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMessage = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);

    setInput('');
    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.text, session_id: sessionId })
      });
      const data = await response.json();
      const botMessage = { sender: 'bot', text: data.answer };
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'bot', text: 'Error getting response.' }]);
    }
  };

  const handleReset = async () => {
    try {
      await fetch(`${API_URL}/reset-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      const newId = crypto.randomUUID();
      setSessionId(newId);
      localStorage.setItem(SESSION_KEY, newId);
      setMessages([]);
      localStorage.removeItem('chat_messages');
    } catch (err) {
      alert('Failed to reset session');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Response copied to clipboard');
  };

  const renderers = {
    a: ({ href, children }) => (
      <a href={href} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    )
  };

  return (
    <div className="chat-container">
      <h2>Chat with UTK</h2>
      <div ref={chatBoxRef} className="chat-box">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.sender}`}>
            <div className="bubble">
              <ReactMarkdown components={renderers}>{msg.text}</ReactMarkdown>
              {msg.sender === 'bot' && (
                <button
                  className="copy-btn"
                  onClick={() => copyToClipboard(msg.text)}
                  title="Copy response"
                >
                  <FaRegCopy />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
        />
        <button onClick={sendMessage} className="send">Send</button>
        <button onClick={handleReset} className="reset">End Session</button>
      </div>
    </div>
  );
}

export default ChatApp;
