import React, { useState } from 'react'; 
import './index.css'; 
import { useNavigate } from 'react-router-dom'; 
import axios from 'axios'; 

const API_BASE_URL = 'http://localhost:8000';


function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post(`${API_BASE_URL}/login`, {
        username: username,
        password: password,
      });

      if (response.data.success) {
        localStorage.setItem('username', username);
        localStorage.setItem('password', password);
        console.log('Login successful:', response.data);
        navigate('/app');
      } else {
        console.error('Login failed:', response.data.error);
      }
    } catch (error) {
      console.error('Error logging in:', error.message);
    }
  };
  const handleRegister = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post(`${API_BASE_URL}/register`, {
        username: username,
        password: password,
      });

      if (response.data.success) {
        const loginResponse = await axios.post(`${API_BASE_URL}/login`, {
          username: username,
          password: password,
        });

        if (loginResponse.data.success) {
          localStorage.setItem('username', username);
          localStorage.setItem('password', password);
          console.log('Registration and login successful');
          navigate('/app');
        }
      } else {
        console.error('Registration failed:', response.data.error);
      }
    } catch (error) {
      console.error('Error registering:', error.message);
    }
  };


  return (
    <>
    <section className='background'>
    <section className='chat-container'>
    <nav><h1>Flights App</h1>
      <ul>
      </ul></nav>

      <nav1 style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <div>
       <h2 style={{ color: 'white', marginBottom: '10px' }}>Login</h2>
      </div>
          <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
            <div style={{ display: "flex", gap: "5px" }}>
              <input
                type="text"
                placeholder="Username"
                value={username}
                withAsterisk
                onChange={(e) => setUsername(e.target.value)}
              />
              <input
                type="password"
                placeholder="Password"
                withAsterisk
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div style={{ display: "flex", gap: "5px", flexDirection: "column" }}>
              <button name="login" type="submit">
                Login
              </button>
              <button name="register" type="button" onClick={handleRegister}>
                Register
              </button>
            </div>
          </form>
        </nav1>
      </section>
      </section>

      </>
  );
}


export default Login;
