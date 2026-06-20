import { useState } from 'react';
import NfcScanner from './NfcScanner';
import DoctorDashboard from './DoctorDashboard';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('scanner');
  const [doctorCode, setDoctorCode] = useState('DOC001');

  // When a successful scan happens, we can automatically switch to their dashboard
  const handleScanSuccess = (data) => {
    if (data && data.doctor_code) {
      setDoctorCode(data.doctor_code);
      setActiveTab('dashboard');
    }
  };

  return (
    <>
      <h1>MedTech Pro</h1>
      
      <div className="glass-panel text-center mb-4" style={{ padding: '1rem' }}>
        <div className="flex justify-between items-center">
          <div className="flex gap-4">
            <button 
              className={`btn ${activeTab === 'scanner' ? '' : 'btn-danger'}`}
              style={activeTab !== 'scanner' ? { background: 'rgba(255,255,255,0.1)', color: 'var(--text-muted)' } : {}}
              onClick={() => setActiveTab('scanner')}
            >
              NFC Scanner
            </button>
            <button 
              className={`btn ${activeTab === 'dashboard' ? '' : 'btn-danger'}`}
              style={activeTab !== 'dashboard' ? { background: 'rgba(255,255,255,0.1)', color: 'var(--text-muted)' } : {}}
              onClick={() => setActiveTab('dashboard')}
            >
              Doctor Dashboard
            </button>
          </div>
          
          <div className="flex items-center gap-4">
            <span style={{ color: 'var(--text-muted)' }}>Current Doctor:</span>
            <input 
              type="text" 
              value={doctorCode} 
              onChange={(e) => setDoctorCode(e.target.value)}
              style={{ width: '120px', margin: 0, padding: '0.5rem' }}
              placeholder="DOC001"
            />
          </div>
        </div>
      </div>

      <div style={{ marginTop: '2rem' }}>
        {activeTab === 'scanner' && <NfcScanner onScanSuccess={handleScanSuccess} />}
        {activeTab === 'dashboard' && <DoctorDashboard doctorCode={doctorCode} />}
      </div>
    </>
  );
}

export default App;
