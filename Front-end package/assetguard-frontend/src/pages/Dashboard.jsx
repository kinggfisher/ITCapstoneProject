import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, tokens, onAuthFailure } from '../api';

export default function Dashboard() {
  const [assets, setAssets] = useState([]);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [locationFilter, setLocationFilter] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (!tokens.getAccess()) { navigate('/'); return; }
    const off = onAuthFailure(() => navigate('/'));

    Promise.all([api.listAssets(), api.listAssessmentHistory()])
      .then(([assetsData, historyData]) => {
        setAssets(assetsData);
        setHistory(historyData);
      })
      .catch((err) => {
        if (err.status !== 401) setError(err.message);
      })
      .finally(() => setHistoryLoading(false));

    return off;
  }, [navigate]);

  return (
    <div className="bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 min-h-screen">
      <nav className="bg-white shadow-sm p-4 flex justify-between items-center mb-8">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gjp rounded-full flex items-center justify-center text-white font-bold">GJP</div>
          <span className="font-bold text-xl">AssetGuard AI</span>
        </div>
        <button
          onClick={() => { api.logout(); navigate('/'); }}
          className="text-red-600 hover:text-red-700 font-medium text-sm transition-colors inline-flex items-center gap-1.5"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15M12 9l-3 3m0 0 3 3m-3-3h12.75" />
          </svg>
          Logout
        </button>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Asset Dashboard</h1>
          <input
            type="text"
            placeholder="Filter by name or location"
            value={locationFilter}
            onChange={(e) => setLocationFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-gjp"
          />
        </div>
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
              {assets.filter(a => a.location_name?.toLowerCase().includes(locationFilter.toLowerCase()) || a.name?.toLowerCase().includes(locationFilter.toLowerCase())).length === 0
              ? <tr><td colSpan="3" className="p-3 text-center text-gray-500">No assets found or loading...</td></tr>
              : null}
            {assets
              .filter(a => a.location_name?.toLowerCase().includes(locationFilter.toLowerCase()) || a.name?.toLowerCase().includes(locationFilter.toLowerCase()))
              .map((asset) => (
              <tr key={asset.id} className="border-b hover:bg-gray-50">
                <td className="p-3 font-medium">{asset.name}</td>
                <td className="p-3">{asset.location_name}</td>
                <td className="p-3">
                  <button onClick={() => navigate(`/request/${asset.id}`)} className="bg-gjp text-white px-4 py-2 rounded inline-flex items-center gap-1.5">
                    Select
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                    </svg>
                  </button>
                </td>
              </tr>
            ))}
            </tbody>
          </table>
        </div>

        {/* History section */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mt-8">
          <h2 className="text-lg font-bold border-b pb-2 mb-4">Your Recent Checks</h2>
          {historyLoading ? (
            <p className="text-gray-400 text-sm animate-pulse">Loading history…</p>
          ) : history.length === 0 ? (
            <p className="text-gray-400 text-sm">No previous checks found.</p>
          ) : (
            <ul className="space-y-3">
              {history.filter(item => item.location_name?.toLowerCase().includes(locationFilter.toLowerCase()) || item.asset_name?.toLowerCase().includes(locationFilter.toLowerCase())).map((item) => (
                <li key={item.id} className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 border">
                  <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${item.is_compliant ? 'bg-green-500' : 'bg-red-500'}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-sm text-gray-900 truncate">{item.asset_name}</span>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full flex-shrink-0 ${item.is_compliant ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {item.is_compliant ? 'PASS' : 'FAIL'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{item.location_name} · {item.load_label}</p>
                    <p className="text-xs text-gray-400">
                      {item.load_value} {item.capacity_metric} &nbsp;/&nbsp; limit {item.capacity_limit} {item.capacity_metric}
                    </p>
                  </div>
                  <span className="text-xs text-gray-400 flex-shrink-0 mt-0.5">
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
