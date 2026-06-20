import React, { useState, useEffect, useRef } from 'react';

function PatientsTab({ doctorCode }) {
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Detail Page States
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [pastReports, setPastReports] = useState([]);
  const [fetchingReports, setFetchingReports] = useState(false);

  // Chatbot States
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [activeFindings, setActiveFindings] = useState({
    risk_level: 'LOW',
    contradictions: [],
    clinical_questions: [],
    missing_evidence: [],
    wearable_observations: [],
    prescription_warnings: [],
    confidence: 1.0
  });

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      const res = await fetch(`http://${window.location.hostname}:5000/api/doctor/${doctorCode}/patients`);
      const result = await res.json();
      if (!res.ok || !result.success) throw new Error(result.message || "Failed to fetch patients");
      setPatients(result.data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientReports = async (patientId) => {
    try {
      setFetchingReports(true);
      const res = await fetch(`http://${window.location.hostname}:5000/api/patient/${patientId}/reports?doctor_code=${doctorCode}`);
      const result = await res.json();
      if (res.ok && result.success) {
        setPastReports(result.data || []);
      }
    } catch (err) {
      console.error("Failed to fetch past reports:", err);
    } finally {
      setFetchingReports(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, [doctorCode]);

  const handlePatientClick = (patientId) => {
    setSelectedPatientId(patientId);
    setSelectedFile(null);
    setUploadSuccess(null);
    setChatMessages([
      {
        sender: 'ai',
        text: `Hello Dr. Sharma! I am your AI Clinical Reasoning Challenger. I have loaded all historical medical and smartwatch data for Patient ${patientId} into my context. Tell me what symptoms or reports you want to analyze.`
      }
    ]);
    setActiveFindings({
      risk_level: 'LOW',
      contradictions: [],
      clinical_questions: [],
      missing_evidence: [],
      wearable_observations: [],
      prescription_warnings: [],
      confidence: 1.0
    });
    fetchPatientReports(patientId);
  };

  const handleUploadReport = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('doctor_code', doctorCode);

    try {
      const res = await fetch(`http://${window.location.hostname}:5000/api/patient/${selectedPatientId}/upload-report`, {
        method: 'POST',
        body: formData
      });

      const result = await res.json();
      if (!res.ok || !result.success) throw new Error(result.message || "Failed to upload report");

      setUploadSuccess({
        filename: result.data.filename,
        hash: result.data.hash,
        preview: result.data.tokenized_preview
      });
      setSelectedFile(null);
      fetchPatientReports(selectedPatientId);
      
      // Auto-post to chat that doctor uploaded a report so AI evaluates it
      setChatMessages(prev => [...prev, { 
        sender: 'user', 
        text: `[System: Uploaded file ${result.data.filename}. Integrity SHA-256 Hash: ${result.data.hash}. Preview: ${result.data.tokenized_preview}]` 
      }]);
      
      // Request AI analysis
      triggerAiChat(`Analyze the newly uploaded file ${result.data.filename}: ${result.data.tokenized_preview}`);

    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      setUploading(false);
    }
  };

  const triggerAiChat = async (messageText) => {
    setChatLoading(true);
    try {
      const res = await fetch(`http://${window.location.hostname}:5000/api/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doctor_code: doctorCode,
          patient_id: selectedPatientId,
          message: messageText,
          chat_history: chatMessages.map(m => `${m.sender}: ${m.text}`)
        })
      });

      const data = await res.json();
      if (res.ok && data.success) {
        setChatMessages(prev => [...prev, { sender: 'ai', text: data.data.response }]);
        if (data.data.findings) {
          setActiveFindings(data.data.findings);
        }
      }
    } catch (err) {
      setChatMessages(prev => [...prev, { sender: 'ai', text: `Failed to analyze: ${err.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleSendChatMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const msg = chatInput;
    setChatMessages(prev => [...prev, { sender: 'user', text: msg }]);
    setChatInput('');
    triggerAiChat(msg);
  };

  const renderBadge = (level) => {
    let color = '#10b981'; // Green for LOW
    if (level === 'MEDIUM') color = '#f59e0b';
    if (level === 'HIGH') color = '#ef4444';
    
    return (
      <span style={{ 
        background: color, 
        color: '#fff', 
        padding: '0.2rem 0.6rem', 
        borderRadius: '20px',
        fontWeight: 'bold',
        fontSize: '0.75rem'
      }}>
        {level} RISK
      </span>
    );
  };

  if (loading) return <div className="text-center p-4">Loading patients...</div>;
  if (error) return <div className="text-center p-4" style={{color: 'var(--danger)'}}>Error: {error}</div>;

  // Master View: List of Patients
  if (!selectedPatientId) {
    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h3>My Assigned Patients</h3>
          <button className="btn" onClick={fetchPatients} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>Refresh List</button>
        </div>

        {patients.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
            {patients.map((p, i) => (
              <div 
                key={i} 
                className="glass-panel" 
                style={{ 
                  padding: '1.5rem', 
                  cursor: 'pointer', 
                  border: '1px solid rgba(255,255,255,0.1)', 
                  transition: 'transform 0.2s',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem'
                }}
                onClick={() => handlePatientClick(p.patient_id)}
                onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.02)'}
                onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
              >
                <div style={{ fontSize: '0.85rem', color: 'var(--accent)', fontWeight: 'bold' }}>PATIENT ACCESS</div>
                <h4 style={{ margin: 0 }}>{p.patient_id}</h4>
                <div className="text-muted" style={{ fontSize: '0.8rem' }}>Assigned: {new Date(p.created_at).toLocaleDateString()}</div>
                <div style={{ marginTop: '1rem', color: '#a78bfa', fontSize: '0.85rem', fontWeight: 'bold' }}>
                  Open Secure Vault & AI Chat &rarr;
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p>No patients assigned yet.</p>
        )}
      </div>
    );
  }

  // Detail View: Patient Page with Secure Report Upload & Contextual AI Chatbot
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Header and Back Button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem' }}>
        <div>
          <button className="btn btn-danger" style={{ padding: '0.4rem 1rem', fontSize: '0.85rem', marginBottom: '0.5rem' }} onClick={() => setSelectedPatientId(null)}>
            &larr; Back to Patient List
          </button>
          <h2 style={{ margin: 0 }}>Patient: {selectedPatientId} Secure Vault</h2>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span style={{ fontSize: '0.8rem', color: '#10b981', background: 'rgba(16, 185, 129, 0.1)', padding: '0.3rem 0.6rem', borderRadius: '4px' }}>
            AES-256-GCM Envelope Encryption Active
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        
        {/* Left Column: Report Upload & History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Upload Section */}
          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <h3 style={{ marginTop: 0, fontSize: '1.1rem', color: 'var(--accent)' }}>Upload Secure Patient Report</h3>
            <p className="text-muted" style={{ fontSize: '0.85rem' }}>
              Draft symptoms, diagnoses, or notes. The vault will auto-generate a SHA-256 hash, encrypt using the patient's AES-256 DEK, and tokenize sensitive terms before RAG embedding.
            </p>

            <form onSubmit={handleUploadReport} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
              <input 
                type="file"
                className="input-field"
                accept=".txt,.md,.json,.csv"
                onChange={e => setSelectedFile(e.target.files[0])}
                disabled={uploading}
                required
                style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.05)', border: '1px dashed var(--glass-border)', color: '#fff' }}
              />
              {selectedFile && (
                <div style={{ fontSize: '0.8rem', color: 'var(--accent)' }}>
                  Selected: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
                </div>
              )}
              <button 
                type="submit" 
                className="btn" 
                style={{ alignSelf: 'flex-start', background: 'linear-gradient(135deg, #10b981, #059669)' }}
                disabled={uploading || !selectedFile}
              >
                {uploading ? "Encrypting & Storing..." : "Upload Secure File"}
              </button>
            </form>

            {uploadSuccess && (
              <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                <span style={{ color: '#34d399', fontWeight: 'bold', fontSize: '0.85rem', display: 'block' }}>Success! Layer 1-10 Security Processed:</span>
                <code style={{ fontSize: '0.75rem', display: 'block', wordBreak: 'break-all', marginTop: '0.5rem', color: '#a7f3d0' }}>
                  SHA-256 Hash: {uploadSuccess.hash}
                </code>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.5rem' }}>
                  <strong>Tokenized Content Preview:</strong> {uploadSuccess.preview}
                </span>
              </div>
            )}
          </div>

          {/* Past Reports List */}
          <div className="glass-panel" style={{ padding: '1.5rem', flex: 1, minHeight: '250px' }}>
            <h3 style={{ marginTop: 0, fontSize: '1.1rem' }}>Decrypted Report History</h3>
            <span className="text-muted" style={{ fontSize: '0.8rem' }}>Consent gate verified on every decryption fetch</span>
            
            {fetchingReports ? (
              <div style={{ marginTop: '1rem' }}>Loading reports...</div>
            ) : pastReports.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1rem', maxHeight: '300px', overflowY: 'auto' }}>
                {pastReports.map((rep, i) => (
                  <div key={i} style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--accent)', marginBottom: '0.25rem' }}>
                      <span>Report #{rep.id.slice(0, 8)}</span>
                      <span>{new Date(rep.created_at).toLocaleString()}</span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.85rem', lineHeight: '1.4' }}>{rep.summary}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted" style={{ fontSize: '0.85rem', marginTop: '1rem' }}>No past reports stored in the vault for this patient.</p>
            )}
          </div>

        </div>

        {/* Right Column: Contextual AI Chatbot & Findings */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '600px', padding: '1.2rem' }}>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.75rem', marginBottom: '0.75rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>AI Clinical Challenger</h3>
              <span className="text-muted" style={{ fontSize: '0.8rem' }}>Verifying against smartwatch & historical reports</span>
            </div>
            {renderBadge(activeFindings.risk_level)}
          </div>

          {/* Chat Messages */}
          <div style={{ flex: 1, overflowY: 'auto', paddingRight: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
            {chatMessages.map((m, idx) => (
              <div 
                key={idx} 
                style={{ 
                  alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '80%',
                  background: m.sender === 'user' ? 'linear-gradient(135deg, #8b5cf6, #6d28d9)' : 'rgba(255, 255, 255, 0.08)',
                  color: '#fff',
                  padding: '0.75rem 1rem',
                  borderRadius: m.sender === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                  fontSize: '0.85rem',
                  lineHeight: '1.4'
                }}
              >
                {m.text}
              </div>
            ))}
            {chatLoading && (
              <div style={{ alignSelf: 'flex-start', background: 'rgba(255, 255, 255, 0.08)', padding: '0.75rem 1rem', borderRadius: '12px 12px 12px 0', fontSize: '0.85rem', color: '#a78bfa' }}>
                Evaluating health indicators & RAG records...
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Safety Warnings Panel overlay or expandable section */}
          {activeFindings.contradictions?.length > 0 || activeFindings.prescription_warnings?.length > 0 ? (
            <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '0.75rem', borderRadius: '6px', marginBottom: '1rem', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
              <span style={{ color: '#ef4444', fontWeight: 'bold', fontSize: '0.8rem', display: 'block', marginBottom: '0.25rem' }}>⚠️ Challenger Warnings:</span>
              <ul style={{ margin: 0, paddingLeft: '1rem', fontSize: '0.75rem', color: '#f87171' }}>
                {activeFindings.contradictions.map((c, i) => <li key={i}>{c}</li>)}
                {activeFindings.prescription_warnings.map((pw, i) => <li key={i}>{pw}</li>)}
              </ul>
            </div>
          ) : null}

          {/* Input Bar */}
          <form onSubmit={handleSendChatMessage} style={{ display: 'flex', gap: '0.5rem' }}>
            <input 
              type="text" 
              className="input-field" 
              placeholder="Ask AI to argue/verify (e.g. 'Is his sleep normal?')" 
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              disabled={chatLoading}
              style={{ margin: 0, fontSize: '0.85rem' }}
            />
            <button type="submit" className="btn" disabled={chatLoading || !chatInput.trim()} style={{ padding: '0 1.2rem', background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)' }}>
              Ask
            </button>
          </form>

        </div>

      </div>

    </div>
  );
}

export default PatientsTab;
