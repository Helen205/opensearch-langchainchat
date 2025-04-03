import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const navigate = useNavigate();
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const username = localStorage.getItem('username');
      const password = localStorage.getItem('password');

      if (!username || !password) {
        setError('Please login again');
        navigate('/');
        return;
      }


      setChatHistory(prev => [...prev, { type: 'user', message: message }]);

      const response = await axios.post(`${API_BASE_URL}/chat`, {
        user_query: message,
        username: username,
        password: password
      });

      console.log('Bot response:', response.data); 

      setChatHistory(prev => [...prev, { type: 'bot', message: response.data.response }]);
      setMessage('');
      setError('');
    } catch (error) {
      console.error('Chat error:', error);
      setError('Mesaj gönderilemedi: ' + (error.response?.data?.detail || error.message));
      if (error.response?.status === 401) {
        navigate('/');
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('username');
    localStorage.removeItem('password');
    navigate('/');
  };

  return (
    <>
      <section className='background'>
        <nav>
          <h1>Flights App</h1>
          <div className="user-info">
            <span style={{color: 'white', marginRight: '40px'}}>User: {localStorage.getItem('username')}</span>
            <button onClick={handleLogout}>Logout</button>
          </div>
        </nav>
        <section className='chat-container'>
          {error && <div className="error-message">{error}</div>}
          <div className="chat-history">
            {chatHistory.map((chat, index) => (
              <div 
                key={index} 
                className={`message ${chat.type === 'user' ? 'user-message' : 'bot-message'}`}
              >
                <div className="message-header">
                  {chat.type === 'user' ? 'You' : 'Bot'}:
                </div>
                <div className="message-content">
                  {chat.message}
                </div>
                <div className="message-time">
                  {new Date().toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
          <form onSubmit={handleSubmit} className="message-input">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your message..."
              className="message-field"
            />
            <button type="submit" className="send-button">Send</button>
          </form>
        </section>
      </section>
    </>
  );
}

export default App;
