import { useState } from 'react';

function NfcScanner({ onScanSuccess }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [scanResult, setScanResult] = useState(null);

  // Hardcoded test data representing a scanned NFC card
  const testNfcData = {
    doctor_code: "DOC001",
    nfc_uid: "TEST_NFC_" + Math.floor(Math.random() * 1000),
    patient_id: "PAT001",
    action: "CHECK_IN",
    scanned_from: "web_frontend"
  };

  const handleScan = async () => {
    setLoading(true);
    setError(null);
    setScanResult(null);

    try {
      const res = await fetch(`http://${window.location.hostname}:5000/api/nfc/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(testNfcData)
      });

      const data = await res.json();
      
      if (!res.ok || !data.success) {
        throw new Error(data.message || "Failed to scan NFC");
      }

      setScanResult(data.data || data);
      if (onScanSuccess) onScanSuccess(data.data || data);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel text-center">
      <h2>NFC Scanner Simulator</h2>
      <p className="mb-4">Click the button below to simulate an NFC card tap for Doctor DOC001.</p>
      
      <button 
        className="btn" 
        onClick={handleScan} 
        disabled={loading}
      >
        {loading ? 'Scanning...' : 'Simulate NFC Tap'}
      </button>

      {error && (
        <div className="mt-4" style={{ color: 'var(--danger)', background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px' }}>
          {error}
        </div>
      )}

      {scanResult && (
        <div className="mt-4" style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          <h3 style={{ color: 'var(--accent)' }}>Scan Successful!</h3>
          <p>Welcome, <strong>{scanResult.doctor_name || scanResult.doctor_code}</strong></p>
          {scanResult.access_count && <p>Access Count: {scanResult.access_count}</p>}
        </div>
      )}
    </div>
  );
}

export default NfcScanner;
