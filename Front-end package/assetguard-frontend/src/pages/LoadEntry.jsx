import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000';

export default function LoadEntry() {
  const { assetId } = useParams();
  const navigate = useNavigate();

  const [asset, setAsset] = useState(null);
  const [equipmentOptions, setEquipmentOptions] = useState([]);
  const [selectedEquipment, setSelectedEquipment] = useState('');
  const [equipmentModel, setEquipmentModel] = useState('');
  const [loadValue, setLoadValue] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null); // { passed: bool, details: {} }

  const token = localStorage.getItem('access_token');

  // Redirect if not logged in
  useEffect(() => {
    if (!token) navigate('/');
  }, [token, navigate]);

  // Fetch asset info + equipment options in parallel
  useEffect(() => {
    const headers = { Authorization: `Bearer ${token}` };

    Promise.all([
      fetch(`${API}/api/assets/${assetId}/`, { headers }).then(r => {
        if (r.status === 401) { navigate('/'); return null; }
        if (!r.ok) throw new Error('Asset not found');
        return r.json();
      }),
      fetch(`${API}/api/equipment-options/`, { headers }).then(r => r.json()),
    ])
      .then(([assetData, optionsData]) => {
        setAsset(assetData);
        setEquipmentOptions(optionsData);
        if (optionsData.length > 0) setSelectedEquipment(optionsData[0].value);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [assetId, token, navigate]);

  const activeOption = equipmentOptions.find(o => o.value === selectedEquipment);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const response = await fetch(`${API}/api/assessments/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          location: asset.location,
          asset: parseInt(assetId),
          equipment_type: selectedEquipment,
          equipment_model: equipmentModel || null,
          load_value: parseFloat(loadValue),
          notes: notes || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Surface validation errors from backend
        const msg = typeof data === 'object'
          ? Object.values(data).flat().join(' ')
          : 'Submission failed.';
        setError(msg);
        return;
      }

      setResult({
        passed: data.is_compliant,
        assessmentId: data.assessment_id,
      });
    } catch (err) {
      setError('Network error. Is the backend running?');
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Loading state ───────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-gray-500 text-lg animate-pulse">Loading asset details…</div>
      </div>
    );
  }

  // ─── Result modal ────────────────────────────────────────────────────────────
  if (result) {
    const passed = result.passed;
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
        <div className={`bg-white rounded-2xl shadow-xl max-w-sm w-full overflow-hidden`}>
          <div className={`p-6 text-center ${passed ? 'bg-green-500' : 'bg-red-500'}`}>
            <div className="text-5xl mb-2">{passed ? '✅' : '⚠️'}</div>
            <h2 className="text-white text-3xl font-black tracking-wide">
              {passed ? 'COMPLIANT' : 'NON-COMPLIANT'}
            </h2>
            <p className="text-white/80 mt-1 text-sm">Assessment #{result.assessmentId}</p>
          </div>
          <div className="p-6 text-center">
            <p className="text-gray-600 text-sm mb-1">
              <span className="font-semibold">{asset?.name}</span> — {asset?.location_name}
            </p>
            <p className="text-gray-500 text-sm">
              {passed
                ? 'The load is within the permitted capacity for this asset.'
                : 'The load exceeds the permitted capacity. An alert has been sent to the responsible party.'}
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="mt-6 w-full bg-gjp hover:bg-[#097a76] text-white font-bold py-3 rounded-xl transition-all"
            >
              Back to Dashboard
            </button>
            {!passed && (
              <button
                onClick={() => { setResult(null); setLoadValue(''); setNotes(''); }}
                className="mt-2 w-full border border-gray-300 text-gray-600 font-semibold py-3 rounded-xl hover:bg-gray-50 transition-all"
              >
                Run Another Check
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ─── Main form ───────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Nav */}
      <nav className="bg-white shadow-sm p-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gjp rounded-full flex items-center justify-center text-white font-bold text-sm">GJP</div>
          <span className="font-bold text-xl">AssetGuard AI</span>
        </div>
        <button
          onClick={() => navigate('/dashboard')}
          className="text-gray-500 hover:text-gray-800 font-medium text-sm flex items-center gap-1 transition-colors"
        >
          ← Back to Dashboard
        </button>
      </nav>

      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Asset info header */}
        <div className="bg-white rounded-xl shadow-sm border p-5 mb-6 flex items-start gap-4">
          <div className="w-10 h-10 bg-gjp/10 rounded-lg flex items-center justify-center text-gjp text-xl flex-shrink-0">🏗</div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">{asset?.name}</h1>
            <p className="text-sm text-gray-500">📍 {asset?.location_name}</p>
          </div>
        </div>

        {/* Form card */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-1">Compliance Check</h2>
          <p className="text-sm text-gray-500 mb-6">
            Enter the equipment load details to check against this asset's rated capacity.
          </p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Equipment type */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Equipment Type <span className="text-red-500">*</span>
              </label>
              <select
                value={selectedEquipment}
                onChange={e => setSelectedEquipment(e.target.value)}
                required
                className="w-full border border-gray-300 p-3 rounded-lg focus:ring-2 focus:ring-gjp outline-none bg-white text-gray-900"
              >
                {equipmentOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              {activeOption && (
                <p className="text-xs text-gray-400 mt-1">
                  Checks against: <span className="font-medium text-gray-600">{activeOption.capacity_name}</span>
                </p>
              )}
            </div>

            {/* Equipment model */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Equipment Model <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <input
                type="text"
                value={equipmentModel}
                onChange={e => setEquipmentModel(e.target.value)}
                placeholder="e.g. Liebherr LTM 1100"
                className="w-full border border-gray-300 p-3 rounded-lg focus:ring-2 focus:ring-gjp outline-none"
              />
            </div>

            {/* Load value */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                {activeOption ? activeOption.load_label : 'Load Value'}
                {activeOption && (
                  <span className="ml-1 text-xs text-gray-400 font-normal">
                    (checked against {activeOption.capacity_name.replace(/_/g, ' ')})
                  </span>
                )}
                <span className="text-red-500"> *</span>
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={loadValue}
                  onChange={e => setLoadValue(e.target.value)}
                  placeholder="Enter value"
                  required
                  className="w-full border border-gray-300 p-3 pr-16 rounded-lg focus:ring-2 focus:ring-gjp outline-none"
                />
                {activeOption && (
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm font-medium pointer-events-none">
                    {activeOption.load_label.toLowerCase().includes('displacement') ? 't' :
                     activeOption.load_label.toLowerCase().includes('axle') ? 't' :
                     activeOption.load_label.toLowerCase().includes('uniform') ? 'kPa' : 'kN'}
                  </span>
                )}
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                Notes <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                rows={3}
                placeholder="Any additional context or observations…"
                className="w-full border border-gray-300 p-3 rounded-lg focus:ring-2 focus:ring-gjp outline-none resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-gjp hover:bg-[#097a76] disabled:opacity-60 text-white font-bold py-4 rounded-xl text-base transition-all"
            >
              {submitting ? 'Checking…' : 'Run Compliance Check'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}