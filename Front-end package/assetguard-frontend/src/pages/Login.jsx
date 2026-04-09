import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await api.login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Login failed. Check backend connection.');
    } finally {
      setSubmitting(false);
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
          <input
            type="text"
            placeholder="Username"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-gjp outline-none"
          />
          <input
            type="password"
            placeholder="Password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-gjp outline-none"
          />
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-gjp hover:bg-[#097a76] disabled:opacity-60 text-white font-bold py-3 rounded-lg transition-all"
          >
            {submitting ? 'Signing in…' : 'Login (Contractor)'}
          </button>
        </form>
      </div>
    </div>
  );
}
