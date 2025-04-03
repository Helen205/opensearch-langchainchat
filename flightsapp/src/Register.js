import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleRegister = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post('http://localhost:8000/register', {
        username: username,
        password: password
      });

      if (response.data.success) {
        console.log('Registration successful:', response.data);
        navigate('/App');
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
    <section className='chat'>
    <nav><h1>Flights App</h1>
          <ul>
      </ul></nav>
      <nav1 style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
       <h2 style={{ color: 'white', marginBottom: '10px' }}>Register</h2>
          <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
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
              value={password} 
              withAsterisk
              onChange={(e) => setPassword(e.target.value)} 
            />
            <button type="submit">Register</button>
          </form>
          <p style={{color: 'white', marginTop: '10px',fontSize: '12px', textDecoration: 'underline' }} onClick={() => navigate('/')}>Already have an account? Login</p>
    </nav1>
    </section>
    </section>
    </>
  );
}

export default Register;
