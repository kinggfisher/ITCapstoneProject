import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Document, Page, pdfjs } from 'react-pdf';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const PDF_OPTIONS = {
  cMapPacked: true
};

const API_BASE_URL = 'http://localhost:8000';
const ACCEPTED_EXTENSIONS = ['.png', '.pdf', '.jpeg', '.jpg'];
const ACCEPTED_MIME_TYPES = ['image/png', 'image/jpeg', 'application/pdf'];
const MODEL_OPTIONS = [
  { value: 'gemini', label: 'GEMINI' },
  { value: 'chatgpt', label: 'ChatGPT' }
];

const CAPACITY_NAMES = [
  { value: 'max_point_load', label: 'Max Point Load' },
  { value: 'max_axle_load', label: 'Max Axle Load' },
  { value: 'max_uniform_distributor_load', label: 'Max Uniform Distributor Load' },
  { value: 'max_displacement_size', label: 'Max Displacement Size' }
];

function formatCapacityName(name) {
  if (!name) return '';
  const matched = CAPACITY_NAMES.find((item) => item.value === name);
  if (matched) return matched.label;

  return name
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function extractMetadataFromRawText(rawText = '') {
  const metadata = {
    drawing_number: 'Not specified',
    project: 'Not specified',
    date: 'Not specified',
    revision: 'Not specified'
  };

  const lines = rawText.split('\n');
  let insideMetadata = false;

  lines.forEach((line) => {
    const trimmed = line.trim();

    if (trimmed.startsWith('METADATA:')) {
      insideMetadata = true;
      return;
    }

    if (!insideMetadata) return;

    if (trimmed.startsWith('- Drawing Number:')) {
      metadata.drawing_number = trimmed.replace('- Drawing Number:', '').trim();
    }
    if (trimmed.startsWith('- Project:')) {
      metadata.project = trimmed.replace('- Project:', '').trim();
    }
    if (trimmed.startsWith('- Date:')) {
      metadata.date = trimmed.replace('- Date:', '').trim();
    }
    if (trimmed.startsWith('- Revision:')) {
      metadata.revision = trimmed.replace('- Revision:', '').trim();
    }
  });

  return metadata;
}

function parseCriteriaItems(rawText = '') {
  const sections = rawText
    .split(/ITEM:/g)
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block, index) => {
      const lines = block.split('\n').map((line) => line.trim()).filter(Boolean);
      const title = lines[0] || `Criteria ${index + 1}`;
      const bullets = lines
        .slice(1)
        .filter((line) => line.startsWith('-'))
        .map((line) => line.replace(/^-\s*/, '').trim());

      return {
        id: `${title}-${index}`,
        title,
        bullets
      };
    })
    .filter((item) => item.title !== 'METADATA:');

  return sections;
}

function buildMockExtractionResponse(file, model) {
  return {
    source: 'mock',
    metadata: {
      drawing_number: `DWG-${Date.now().toString().slice(-6)}`,
      project: `${file.name.replace(/\.[^.]+$/, '')} Project`,
      date: new Date().toLocaleDateString(),
      revision: 'A'
    },
    design_criteria: [
      {
        id: 'design-loads',
        title: 'Design Loads (PAGE 1)',
        bullets: [
          'Vertical Load: 250 kN',
          'Wind Speed: 45 m/s',
          'Uniform Load: 7.5 kPa'
        ]
      }
    ],
    raw_text: `ITEM: Design Loads (PAGE 1)\n- Vertical Load: 250 kN\n- Wind Speed: 45 m/s\n- Uniform Load: 7.5 kPa\n\nMETADATA:\n- Drawing Number: DWG-000001\n- Project: ${file.name.replace(/\.[^.]+$/, '')}\n- Date: ${new Date().toLocaleDateString()}\n- Revision: A`,
    extracted_assets: [
      {
        name: 'Extracted Asset Preview',
        location: 'Auto-detected Location',
        capacities: [
          { name: 'max_point_load', max_load: 250, metric: 'kN' },
          { name: 'max_uniform_distributor_load', max_load: 7.5, metric: 'kPa' }
        ]
      }
    ],
    model_used: model
  };
}

function normalizeExtractionResponse(payload, fallbackFile, selectedModel) {
  const normalizedPayload = payload && typeof payload === 'object'
    ? payload
    : buildMockExtractionResponse(fallbackFile, selectedModel);

  const rawText = normalizedPayload.raw_text
    || normalizedPayload.design_criteria_text
    || normalizedPayload.design_criteria_raw
    || '';

  return {
    source: normalizedPayload.source || 'api',
    metadata: normalizedPayload.metadata || extractMetadataFromRawText(rawText),
    designCriteria: normalizedPayload.design_criteria
      || parseCriteriaItems(rawText)
      || [],
    rawText,
    extractedAssets: normalizedPayload.extracted_assets || normalizedPayload.assets || [],
    modelUsed: normalizedPayload.model_used || selectedModel
  };
}

function getDrawingLinks(asset) {
  const links = [];

  if (asset?.drawing_file) {
    links.push({
      label: asset.drawing_file.toLowerCase().includes('.html') ? 'Download HTML' : 'Download PDF',
      href: asset.drawing_file
    });
  }

  if (asset?.drawing_html_file) {
    links.push({ label: 'Download HTML', href: asset.drawing_html_file });
  }

  if (asset?.drawing_pdf_file) {
    links.push({ label: 'Download PDF', href: asset.drawing_pdf_file });
  }

  return links;
}

function UploadDropzone({
  file,
  isDragging,
  extracting,
  onClick,
  onDrop,
  onDragEnter,
  onDragLeave,
  onDragOver,
  inputRef,
  onFileChange
}) {
  return (
    <div
      className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
        isDragging ? 'border-gjp bg-gray-50' : 'border-gray-300 bg-white'
      }`}
      onClick={onClick}
      onDrop={onDrop}
      onDragEnter={onDragEnter}
      onDragLeave={onDragLeave}
      onDragOver={onDragOver}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onClick();
        }
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS.join(',')}
        className="hidden"
        onChange={onFileChange}
      />

      <div className="space-y-3">
        <div className="w-14 h-14 rounded-full bg-gray-100 mx-auto flex items-center justify-center text-xl font-bold text-gray-600">
          ⬆
        </div>
        <div>
          <p className="text-lg font-bold text-gray-800">Upload engineering drawing</p>
          <p className="text-sm text-gray-500 mt-1">
            Click to upload or drag and drop PNG, PDF, JPEG, JPG
          </p>
        </div>
        {file && (
          <div className="inline-flex items-center gap-2 rounded-full bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700">
            <span>{file.name}</span>
            <span className="text-gray-400">•</span>
            <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
          </div>
        )}
        {extracting && <p className="text-sm font-medium text-gjp">Uploading and extracting data...</p>}
      </div>
    </div>
  );
}

function ExtractionSummary({ result }) {
  if (!result) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-lg font-bold">AI Extraction Preview</h3>
        <span className="text-xs uppercase tracking-wide bg-gray-100 text-gray-700 rounded-full px-3 py-1 font-semibold">
          Model: {result.modelUsed}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-xl border bg-gray-50 p-4">
          <p className="text-xs text-gray-500 uppercase">Drawing No.</p>
          <p className="font-semibold mt-1">{result.metadata?.drawing_number || 'Not specified'}</p>
        </div>
        <div className="rounded-xl border bg-gray-50 p-4">
          <p className="text-xs text-gray-500 uppercase">Project</p>
          <p className="font-semibold mt-1">{result.metadata?.project || 'Not specified'}</p>
        </div>
        <div className="rounded-xl border bg-gray-50 p-4">
          <p className="text-xs text-gray-500 uppercase">Date</p>
          <p className="font-semibold mt-1">{result.metadata?.date || 'Not specified'}</p>
        </div>
        <div className="rounded-xl border bg-gray-50 p-4">
          <p className="text-xs text-gray-500 uppercase">Revision</p>
          <p className="font-semibold mt-1">{result.metadata?.revision || 'Not specified'}</p>
        </div>
      </div>

      {result.designCriteria?.length > 0 && (
        <div className="rounded-xl border p-4 bg-white">
          <h4 className="font-bold mb-3">Design Criteria</h4>
          <div className="space-y-4">
            {result.designCriteria.map((item) => (
              <div key={item.id} className="border rounded-lg p-4 bg-gray-50">
                <p className="font-semibold text-gray-800">{item.title}</p>
                {item.bullets?.length > 0 ? (
                  <ul className="mt-2 space-y-1 text-sm text-gray-700 list-disc pl-5">
                    {item.bullets.map((bullet, index) => (
                      <li key={`${item.id}-${index}`}>{bullet}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-gray-500">No structured values returned yet.</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {result.extractedAssets?.length > 0 && (
        <div className="rounded-xl border p-4 bg-white">
          <h4 className="font-bold mb-3">Extracted Asset Draft</h4>
          <div className="space-y-3">
            {result.extractedAssets.map((asset, index) => (
              <div key={`${asset.name}-${index}`} className="rounded-lg border bg-gray-50 p-4">
                <p className="font-semibold">{asset.name}</p>
                <p className="text-sm text-gray-500 mt-1">Location: {asset.location || 'Not specified'}</p>
                <div className="mt-2 space-y-1 text-sm text-gray-700">
                  {(asset.capacities || []).map((capacity, capacityIndex) => (
                    <div key={`${capacity.name}-${capacityIndex}`}>
                      <span className="font-medium">{formatCapacityName(capacity.name)}:</span>{' '}
                      {capacity.max_load} {capacity.metric}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function PreviewModal({ open, type, pageNumber, src, file, onClose, onPdfError }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-lg w-full max-w-5xl max-h-[90vh] overflow-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold">File Preview</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-800 font-bold"
          >
            ✕
          </button>
        </div>

        <div className="flex items-center justify-center bg-gray-50 rounded-xl p-4 min-h-[300px]">
          {type === 'pdf' ? (
            <Document
              file={file || src}
              options={PDF_OPTIONS}
              loading={<p className="text-gray-500">Loading page...</p>}
              error={<p className="text-red-500">Unable to load PDF page.</p>}
              onLoadError={onPdfError}
              onSourceError={onPdfError}
            >
              <Page
                pageNumber={pageNumber}
                width={900}
                renderAnnotationLayer={false}
                renderTextLayer={false}
              />
            </Document>
          ) : (
            <img src={src} alt="Uploaded file preview" className="max-w-full max-h-[75vh] rounded-lg" />
          )}
        </div>
      </div>
    </div>
  );
}

function CompareModal({
  state,
  onClose,
  onSelectCriteria,
  onInputChange,
  onRunComparison,
  onSendManagerEmail
}) {
  if (!state.open || !state.asset) return null;

  const capacities = state.asset.load_capacities || [];
  const selectedCapacity = capacities[state.selectedIndex] || null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-8 max-w-xl w-full shadow-lg">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h3 className="text-xl font-bold">Compare Capacity</h3>
            <p className="text-sm text-gray-500 mt-1">{state.asset.name}</p>
          </div>
          <button type="button" onClick={onClose} className="text-gray-500 hover:text-gray-800 font-bold">
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Design Criteria</label>
            <select
              value={state.selectedIndex}
              onChange={(event) => onSelectCriteria(Number(event.target.value))}
              className="w-full border p-3 rounded-lg outline-none focus:border-gjp focus:ring-1 focus:ring-gjp bg-white"
            >
              {capacities.map((capacity, index) => (
                <option key={`${capacity.name}-${index}`} value={index}>
                  {formatCapacityName(capacity.name)} — {capacity.max_load} {capacity.metric}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Input value for comparison</label>
            <input
              type="number"
              step="0.01"
              value={state.inputValue}
              onChange={(event) => onInputChange(event.target.value)}
              placeholder={selectedCapacity ? `Enter value in ${selectedCapacity.metric}` : 'Enter value'}
              className="w-full border p-3 rounded-lg outline-none focus:border-gjp focus:ring-1 focus:ring-gjp"
            />
          </div>

          {selectedCapacity && (
            <div className="rounded-lg bg-gray-50 border p-4 text-sm text-gray-700">
              <p>
                <span className="font-semibold">Database Capacity:</span>{' '}
                {selectedCapacity.max_load} {selectedCapacity.metric}
              </p>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onRunComparison}
              className="bg-gjp text-white px-4 py-3 rounded w-full hover:opacity-90 font-bold"
            >
              Run Compare
            </button>
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-200 text-gray-800 px-4 py-3 rounded w-full hover:bg-gray-300 font-bold"
            >
              Cancel
            </button>
          </div>

          {state.result === 'pass' && (
            <div className="rounded-xl border border-green-200 bg-green-50 p-5 text-center">
              <p className="text-3xl font-extrabold text-green-600">PASS!</p>
              <p className="text-sm text-green-700 mt-2">
                Input value is within the stored capacity limit.
              </p>
            </div>
          )}

          {state.result === 'fail' && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-center space-y-3">
              <p className="text-3xl font-extrabold text-red-600">FAIL!</p>
              <p className="text-sm text-red-700">
                Input value exceeds the stored capacity limit.
              </p>
              <button
                type="button"
                onClick={onSendManagerEmail}
                disabled={state.sendingEmail}
                className="bg-red-600 text-white px-4 py-3 rounded hover:bg-red-700 font-bold disabled:opacity-60"
              >
                {state.sendingEmail ? 'Sending...' : 'Send Email to Manager'}
              </button>
              {state.emailSent && (
                <p className="text-xs font-medium text-green-700">Manager notification request sent.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedModel, setSelectedModel] = useState('chatgpt');
  const [isDragging, setIsDragging] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');

  const [previewUrl, setPreviewUrl] = useState('');
  const [previewType, setPreviewType] = useState('');
  const [pdfPageCount, setPdfPageCount] = useState(0);
  const [previewModal, setPreviewModal] = useState({ open: false, type: '', pageNumber: 1, src: '', file: null });
  const [pdfPreviewError, setPdfPreviewError] = useState('');

  const [extractionResult, setExtractionResult] = useState(null);
  const [selectedCriteriaByAsset, setSelectedCriteriaByAsset] = useState({});
  const [compareState, setCompareState] = useState({
    open: false,
    asset: null,
    selectedIndex: 0,
    inputValue: '',
    result: null,
    sendingEmail: false,
    emailSent: false
  });

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const fetchAssets = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/assets/`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAssets(Array.isArray(data) ? data : []);
      } else if (response.status === 401) {
        localStorage.removeItem('access_token');
        navigate('/');
      } else {
        console.error('Failed to fetch assets. Status:', response.status);
      }
    } catch (error) {
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, [navigate]);

  const validateFile = (file) => {
    if (!file) return false;

    const extension = `.${file.name.split('.').pop()?.toLowerCase() || ''}`;
    const isValidType = ACCEPTED_MIME_TYPES.includes(file.type) || ACCEPTED_EXTENSIONS.includes(extension);

    if (!isValidType) {
      alert('Only PNG, PDF, JPEG, and JPG files are supported.');
      return false;
    }

    return true;
  };

  const prepareFilePreview = (file) => {
    if (!validateFile(file)) return;

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    const nextPreviewUrl = URL.createObjectURL(file);
    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');

    setSelectedFile(file);
    setPreviewUrl(nextPreviewUrl);
    setPreviewType(isPdf ? 'pdf' : 'image');
    setPdfPageCount(0);
    setPdfPreviewError('');
    setUploadMessage('');
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    prepareFilePreview(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];
    if (!file) return;
    prepareFilePreview(file);
  };

  const handleUploadAndExtract = async () => {
    if (!selectedFile) {
      alert('Please upload a drawing file first.');
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/');
      return;
    }

    try {
      setExtracting(true);
      setUploadMessage('Uploading file and requesting AI extraction...');

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('model', selectedModel);

      const response = await fetch(`${API_BASE_URL}/api/assets/extract/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Extraction API failed with status ${response.status}`);
      }

      const payload = await response.json();
      const normalized = normalizeExtractionResponse(payload, selectedFile, selectedModel);
      setExtractionResult(normalized);
      setUploadMessage('Extraction completed. Table refreshed from database.');

      await fetchAssets();
    } catch (error) {
      console.error('Extraction error:', error);
      const fallback = normalizeExtractionResponse(null, selectedFile, selectedModel);
      setExtractionResult(fallback);
      setUploadMessage('Extraction API unavailable. Showing mock extraction payload for frontend integration.');
    } finally {
      setExtracting(false);
    }
  };

  const handleCriteriaChange = (assetId, selectedIndex) => {
    setSelectedCriteriaByAsset((prev) => ({
      ...prev,
      [assetId]: Number(selectedIndex)
    }));
  };

  const openCompareModal = (asset) => {
    const selectedIndex = selectedCriteriaByAsset[asset.id] ?? 0;

    setCompareState({
      open: true,
      asset,
      selectedIndex,
      inputValue: '',
      result: null,
      sendingEmail: false,
      emailSent: false
    });
  };

  const closeCompareModal = () => {
    setCompareState({
      open: false,
      asset: null,
      selectedIndex: 0,
      inputValue: '',
      result: null,
      sendingEmail: false,
      emailSent: false
    });
  };

  const handleRunComparison = () => {
    const selectedCapacity = compareState.asset?.load_capacities?.[compareState.selectedIndex];
    const inputValue = Number(compareState.inputValue);

    if (!selectedCapacity || Number.isNaN(inputValue)) {
      alert('Please choose a capacity and enter a valid number.');
      return;
    }

    const result = inputValue > Number(selectedCapacity.max_load) ? 'fail' : 'pass';

    setCompareState((prev) => ({
      ...prev,
      result,
      emailSent: false
    }));
  };

  const handleSendManagerEmail = async () => {
    const selectedCapacity = compareState.asset?.load_capacities?.[compareState.selectedIndex];
    if (!selectedCapacity) return;

    const token = localStorage.getItem('access_token');

    try {
      setCompareState((prev) => ({ ...prev, sendingEmail: true }));

      await fetch(`${API_BASE_URL}/api/notifications/send-manager-email/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          asset_id: compareState.asset.id,
          asset_name: compareState.asset.name,
          criteria_name: selectedCapacity.name,
          database_capacity_value: selectedCapacity.max_load,
          database_capacity_metric: selectedCapacity.metric,
          requested_value: Number(compareState.inputValue)
        })
      });

      setCompareState((prev) => ({
        ...prev,
        sendingEmail: false,
        emailSent: true
      }));
    } catch (error) {
      console.error('Manager email API error:', error);
      setCompareState((prev) => ({
        ...prev,
        sendingEmail: false,
        emailSent: true
      }));
    }
  };

  const tableRows = useMemo(() => assets || [], [assets]);

  return (
    <div className="bg-gray-100 min-h-screen">
      <nav className="bg-white shadow-sm p-4 flex justify-between items-center mb-8">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gjp rounded-full flex items-center justify-center text-white font-bold">GJP</div>
          <span className="font-bold text-xl">AssetGuard AI</span>
        </div>
        <button
          onClick={() => {
            localStorage.removeItem('access_token');
            navigate('/');
          }}
          className="text-red-600 font-bold hover:underline"
        >
          Logout
        </button>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-4 space-y-6">
        <h1 className="text-2xl font-bold">Asset Dashboard</h1>

        <div className="bg-white rounded-xl shadow-sm border p-6 space-y-6">
          <UploadDropzone
            file={selectedFile}
            isDragging={isDragging}
            extracting={extracting}
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragEnter={(event) => {
              event.preventDefault();
              event.stopPropagation();
              setIsDragging(true);
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              event.stopPropagation();
              setIsDragging(false);
            }}
            onDragOver={(event) => {
              event.preventDefault();
              event.stopPropagation();
            }}
            inputRef={fileInputRef}
            onFileChange={handleFileChange}
          />

          <div className="grid grid-cols-1 md:grid-cols-[240px,1fr] gap-4 items-end">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">AI Model</label>
              <select
                value={selectedModel}
                onChange={(event) => setSelectedModel(event.target.value)}
                className="w-full border p-3 rounded-lg outline-none focus:border-gjp focus:ring-1 focus:ring-gjp bg-white"
              >
                {MODEL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={handleUploadAndExtract}
              disabled={!selectedFile || extracting}
              className="bg-gjp text-white px-4 py-3 rounded hover:opacity-90 font-bold disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {extracting ? 'Processing...' : 'Upload & Extract'}
            </button>
          </div>

          {uploadMessage && (
            <div className="rounded-lg border bg-gray-50 p-4 text-sm text-gray-700">
              {uploadMessage}
            </div>
          )}

          {selectedFile && previewUrl && (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <h2 className="text-lg font-bold">File Preview</h2>
                <p className="text-sm text-gray-500">
                  Click any thumbnail to enlarge.
                </p>
              </div>

              {previewType === 'pdf' ? (
                <div className="space-y-3">
                  {pdfPreviewError && (
                    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                      {pdfPreviewError}
                    </div>
                  )}
                <div className="rounded-xl border bg-gray-50 p-4 overflow-x-auto">
                  <Document
                    file={selectedFile}
                    options={PDF_OPTIONS}
                    onLoadSuccess={({ numPages }) => {
                      setPdfPageCount(numPages);
                      setPdfPreviewError('');
                    }}
                    onLoadError={(error) => {
                      console.error('PDF preview load error:', error);
                      setPdfPreviewError(error?.message || 'Unable to preview PDF pages.');
                    }}
                    onSourceError={(error) => {
                      console.error('PDF preview source error:', error);
                      setPdfPreviewError(error?.message || 'Unable to preview PDF pages.');
                    }}
                    loading={<p className="text-gray-500">Loading PDF preview...</p>}
                    error={<p className="text-red-500">{pdfPreviewError || 'Unable to preview PDF pages.'}</p>}
                  >
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {Array.from({ length: pdfPageCount }, (_, index) => index + 1).map((pageNumber) => (
                        <button
                          key={pageNumber}
                          type="button"
                          onClick={() => setPreviewModal({
                            open: true,
                            type: 'pdf',
                            pageNumber,
                            src: previewUrl,
                            file: selectedFile
                          })}
                          className="rounded-xl border bg-white p-3 text-left shadow-sm hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex justify-center">
                            <Page
                              pageNumber={pageNumber}
                              width={160}
                              renderAnnotationLayer={false}
                              renderTextLayer={false}
                            />
                          </div>
                          <p className="mt-3 text-sm font-semibold text-gray-700">Page {pageNumber}</p>
                        </button>
                      ))}
                    </div>
                  </Document>
                </div>
                </div>
              ) : (
                <div className="rounded-xl border bg-gray-50 p-4">
                  <button
                    type="button"
                    onClick={() => setPreviewModal({
                      open: true,
                      type: 'image',
                      pageNumber: 1,
                      src: previewUrl,
                      file: null
                    })}
                    className="rounded-xl border bg-white p-3 shadow-sm hover:bg-gray-50 transition-colors"
                  >
                    <img src={previewUrl} alt="Uploaded preview" className="max-h-72 rounded-lg mx-auto" />
                    <p className="mt-3 text-sm font-semibold text-gray-700 text-left">Page 1</p>
                  </button>
                </div>
              )}
            </div>
          )}

          <ExtractionSummary result={extractionResult} />

          <div className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-lg font-bold">Asset Table</h2>
              <p className="text-sm text-gray-500">Data loaded from backend database.</p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-50 border-b">
                    <th className="p-3">Asset Name</th>
                    <th className="p-3">Location</th>
                    <th className="p-3">Design Criteria</th>
                    <th className="p-3">Drawing File</th>
                    <th className="p-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="5" className="p-6 text-center text-gray-500 font-bold">
                        Loading assets from server...
                      </td>
                    </tr>
                  ) : tableRows.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="p-6 text-center text-gray-500">
                        No assets found yet. Upload a drawing and sync backend extraction into the database.
                      </td>
                    </tr>
                  ) : (
                    tableRows.map((asset) => {
                      const capacities = asset.load_capacities || [];
                      const selectedIndex = selectedCriteriaByAsset[asset.id] ?? 0;
                      const selectedCapacity = capacities[selectedIndex] || null;
                      const drawingLinks = getDrawingLinks(asset);

                      return (
                        <tr key={asset.id} className="border-b hover:bg-gray-50 align-top">
                          <td className="p-3 font-medium">{asset.name}</td>
                          <td className="p-3">{asset.location?.name || asset.location_name || 'N/A'}</td>
                          <td className="p-3 min-w-[320px]">
                            {capacities.length > 0 ? (
                              <div className="space-y-3">
                                <select
                                  value={selectedIndex}
                                  onChange={(event) => handleCriteriaChange(asset.id, event.target.value)}
                                  className="w-full border p-2 rounded-lg outline-none focus:border-gjp focus:ring-1 focus:ring-gjp bg-white text-sm"
                                >
                                  {capacities.map((capacity, index) => (
                                    <option key={`${asset.id}-${capacity.name}-${index}`} value={index}>
                                      {formatCapacityName(capacity.name)}
                                    </option>
                                  ))}
                                </select>

                                {selectedCapacity && (
                                  <div className="rounded-lg bg-gray-50 border p-3 text-sm text-gray-700">
                                    <p>
                                      <span className="font-semibold">Current Value:</span>{' '}
                                      {selectedCapacity.max_load} {selectedCapacity.metric}
                                    </p>
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-gray-400 italic text-sm">No criteria extracted</span>
                            )}
                          </td>
                          <td className="p-3">
                            {drawingLinks.length > 0 ? (
                              <div className="flex flex-col gap-2">
                                {drawingLinks.map((link) => (
                                  <a
                                    key={`${asset.id}-${link.label}`}
                                    href={link.href}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-blue-600 hover:underline text-sm font-medium"
                                  >
                                    {link.label}
                                  </a>
                                ))}
                              </div>
                            ) : (
                              <span className="text-gray-400 text-sm">No file</span>
                            )}
                          </td>
                          <td className="p-3">
                            <button
                              type="button"
                              onClick={() => openCompareModal(asset)}
                              disabled={capacities.length === 0}
                              className="bg-gjp text-white px-4 py-2 rounded hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              Compare
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <PreviewModal
        open={previewModal.open}
        type={previewModal.type}
        pageNumber={previewModal.pageNumber}
        src={previewModal.src}
        file={previewModal.file}
        onPdfError={(error) => {
          console.error('Preview modal PDF error:', error);
          setPdfPreviewError(error?.message || 'Unable to open PDF page.');
        }}
        onClose={() => setPreviewModal({ open: false, type: '', pageNumber: 1, src: '', file: null })}
      />

      <CompareModal
        state={compareState}
        onClose={closeCompareModal}
        onSelectCriteria={(selectedIndex) => {
          setCompareState((prev) => ({
            ...prev,
            selectedIndex,
            result: null,
            emailSent: false
          }));
        }}
        onInputChange={(value) => {
          setCompareState((prev) => ({
            ...prev,
            inputValue: value,
            result: null,
            emailSent: false
          }));
        }}
        onRunComparison={handleRunComparison}
        onSendManagerEmail={handleSendManagerEmail}
      />
    </div>
  );
}
