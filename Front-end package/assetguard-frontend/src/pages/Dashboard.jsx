import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, tokens, onAuthFailure } from '../api';

export default function Dashboard() {
  const [assets, setAssets] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (!tokens.getAccess()) { navigate('/'); return; }
    const off = onAuthFailure(() => navigate('/'));

    api.listAssets()
      .then(setAssets)
      .catch((err) => {
        if (err.status !== 401) setError(err.message);
      });

    return off;
  }, [navigate]);

  return (
    <div className="bg-gray-100 min-h-screen">
      <nav className="bg-white shadow-sm p-4 flex justify-between items-center mb-8">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gjp rounded-full flex items-center justify-center text-white font-bold">GJP</div>
          <span className="font-bold text-xl">AssetGuard AI</span>
        </div>
        <button onClick={() => { api.logout(); navigate('/'); }} className="text-red-600 font-bold">Logout</button>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-4">
        <h1 className="text-2xl font-bold mb-6">Asset Dashboard</h1>
        {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-bold border-b pb-2 mb-4">Select Asset for Load Request</h2>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="p-3">Asset Name</th>
                <th className="p-3">Location</th>
                <th className="p-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {assets.length === 0 ? <tr><td colSpan="3" className="p-3 text-center text-gray-500">No assets found or loading...</td></tr> : null}
              {assets.map((asset) => (
                <tr key={asset.id} className="border-b hover:bg-gray-50">
                  <td className="p-3 font-medium">{asset.name}</td>
                  <td className="p-3">{asset.location_name}</td>
                  <td className="p-3">
                    <button onClick={() => navigate(`/request/${asset.id}`)} className="bg-gjp text-white px-4 py-2 rounded">Select</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
