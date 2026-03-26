import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

export default function LoadEntry() {
  const { assetId } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ equipment_type: 'Excavator', weight_kg: '' });
  const [modal, setModal] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('access_token');
    
    try {
      const response = await fetch('http://localhost:8000/api/compliance-check/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ asset_id: assetId, ...formData })
      });
      
      const data = await response.json();
      setModal({ status: data.is_compliant ? 'PASSED' : 'FAILED' });
    } catch (error) {
      console.error("Error:", error);
      // 联调期间，如果后端还没写好这个接口，可以用下面这行假数据测试弹窗效果
      // setModal({ status: 'FAILED' });
    }
  };

  return (
    <div className="bg-gray-100 min-h-screen py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <button onClick={() => navigate('/dashboard')} className="text-gray-600 mb-4 font-medium">← Back to Dashboard</button>
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold mb-6">Load Request Entry (Asset: {assetId})</h2>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <input type="number" placeholder="Total Weight (kg)" required onChange={(e) => setFormData({...formData, weight_kg: e.target.value})} className="border p-3 rounded-lg focus:ring-2 focus:ring-gjp outline-none" />
              <select onChange={(e) => setFormData({...formData, equipment_type: e.target.value})} className="border p-3 rounded-lg focus:ring-2 focus:ring-gjp outline-none">
                <option value="Excavator">Excavator</option>
                <option value="Scissor Lift">Scissor Lift</option>
              </select>
            </div>
            <button type="submit" className="w-full bg-gjp text-white font-bold py-4 rounded-lg">Run Compliance Check</button>
          </form>
        </div>
      </div>

      {modal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className={`bg-white rounded-xl p-8 max-w-sm w-full text-center border-t-8 ${modal.status === 'FAILED' ? 'border-red-500' : 'border-green-500'}`}>
            <h3 className={`text-2xl font-bold ${modal.status === 'FAILED' ? 'text-red-600' : 'text-green-600'}`}>{modal.status}</h3>
            <button onClick={() => navigate('/dashboard')} className="mt-6 w-full bg-gray-100 py-3 rounded-lg font-bold">Close & Return</button>
          </div>
        </div>
      )}
    </div>
  );
}