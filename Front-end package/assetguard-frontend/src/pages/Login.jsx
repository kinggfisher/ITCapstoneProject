import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/api/token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: email, password: password })
      });

      if (!response.ok) throw new Error('Invalid credentials');
      
      const data = await response.json();
      localStorage.setItem('access_token', data.access); // 保存后端给的 Token
      navigate('/dashboard'); // 登录成功跳走
    } catch (err) {
      setError("Login failed. Check backend connection.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-cover bg-center" style={{ backgroundImage: "url('/pic.jpg')" }}>
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <img src="/pic1.jpg" alt="Logo" className="h-20 mx-auto mb-4 object-contain" />
          <h2 className="text-2xl font-bold text-gray-800">AssetGuard AI</h2>
        </div>
        {error && <p className="text-red-500 text-center mb-4">{error}</p>}
        <form onSubmit={handleLogin} className="space-y-6">
          <input type="email" placeholder="Email" required onChange={(e) => setEmail(e.target.value)} className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-gjp outline-none" />
          <input type="password" placeholder="Password" required onChange={(e) => setPassword(e.target.value)} className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-gjp outline-none" />
          <button type="submit" className="w-full bg-gjp hover:bg-[#097a76] text-white font-bold py-3 rounded-lg transition-all">
            Login (Contractor)
          </button>
        </form>
      </div>
    </div>
  );
}