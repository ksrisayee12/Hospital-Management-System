import React, { useState, useRef, useEffect } from 'react';

function AiReviewTab({ doctorCode }) {
  const [patientId, setPatientId] = useState('PAT001');
  const [messages, setMessages] = useState([
    { 
      sender: 'ai', 
      text: 'Hello Dr. Sharma! I am your AI Clinical Reasoning Challenger. I review your diagnostics and prescriptions using patient smartwatch data and past reports. What are we drafting today?' 
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
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
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = inputValue;
    setMessages(prev => [...prev, { sender: 'user', text: userMessage }]);
    setInputValue('');
    setLoading(true);

    try {
      const res = await fetch(`http://${window.location.hostname}:5000/api/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doctor_code: doctorCode,
          patient_id: patientId,
          message: userMessage,
          chat_history: messages.map(m => `${m.sender}: ${m.text}`)
        })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.message || 'Failed to communicate with AI');
      }

      setMessages(prev => [...prev, { sender: 'ai', text: data.data.response }]);
      if (data.data.findings) {
        setActiveFindings(data.data.findings);
      }
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'ai', text: `System Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const renderBadge = (level) => {
    let color = '#10b981'; // Green for LOW
    if (level === 'MEDIUM') color = '#f59e0b';
    if (level === 'HIGH') color = '#ef4444';
    
    return (
      <span style={{ 
        background: color, 
        color: '#fff', 
        padding: '0.25rem 0.6rem', 
        borderRadius: '20px',
        fontWeight: 'bold',
        fontSize: '0.75rem',
        letterSpacing: '0.05em'
      }}>
        {level} RISK
      </span>
    );
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '1.5rem', height: '70vh' }}>
      
      {/* Left Panel: Chatbot Interface */}
      <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.75rem', marginBottom: '0.75rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Clinical Challenger Bot</h3>
            <span className="text-muted" style={{ fontSize: '0.8rem' }}>Assisting with Patient Sovereign Intelligence</span>
          </div>
          <div>
            <label style={{ marginRight: '0.5rem', fontSize: '0.85rem' }}>Active Patient:</label>
            <input 
              type="text" 
              value={patientId} 
              onChange={e => setPatientId(e.target.value)} 
              style={{ width: '80px', padding: '0.2rem 0.4rem', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', borderRadius: '4px', textAlign: 'center' }}
            />
          </div>
        </div>

        {/* Message Container */}
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
          {messages.map((m, idx) => (
            <div 
              key={idx} 
              style={{ 
                alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '75%',
                background: m.sender === 'user' ? 'linear-gradient(135deg, #8b5cf6, #6d28d9)' : 'rgba(255, 255, 255, 0.08)',
                color: '#fff',
                padding: '0.75rem 1rem',
                borderRadius: m.sender === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                fontSize: '0.9rem',
                lineHeight: '1.4',
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
              }}
            >
              {m.text}
            </div>
          ))}
          {loading && (
            <div style={{ alignSelf: 'flex-start', background: 'rgba(255, 255, 255, 0.08)', padding: '0.75rem 1rem', borderRadius: '12px 12px 12px 0', fontSize: '0.9rem', color: '#a78bfa', fontWeight: 'bold' }}>
              AI Challenger is evaluating RAG context...
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: '0.5rem' }}>
          <input 
            type="text" 
            className="input-field" 
            placeholder="Type your diagnostic note or prescription (e.g. 'Prescribing Metformin 5000mg')" 
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            disabled={loading}
            style={{ margin: 0 }}
          />
          <button type="submit" className="btn" disabled={loading || !inputValue.trim()} style={{ padding: '0 1.5rem', background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)' }}>
            Send
          </button>
        </form>
      </div>

      {/* Right Panel: AI Review Board / Live Findings */}
      <div className="glass-panel" style={{ overflowY: 'auto', padding: '1rem', borderLeft: '1px solid rgba(255,255,255,0.05)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h4 style={{ margin: 0, color: 'var(--accent)' }}>Live Safety Findings</h4>
          {renderBadge(activeFindings.risk_level)}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          
          <div>
            <span style={{ fontSize: '0.8rem', color: '#ef4444', fontWeight: 'bold', display: 'block', marginBottom: '0.25rem' }}>Contradictions</span>
            {activeFindings.contradictions?.length > 0 ? (
              <ul style={{ paddingLeft: '1rem', margin: 0, fontSize: '0.85rem', color: '#f87171' }}>
                {activeFindings.contradictions.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            ) : <p className="text-muted" style={{ fontSize: '0.85rem', margin: 0 }}>No contradictions detected.</p>}
          </div>

          <hr style={{ border: '0', borderTop: '1px solid rgba(255,255,255,0.05)', margin: 0 }} />

          <div>
            <span style={{ fontSize: '0.8rem', color: '#f59e0b', fontWeight: 'bold', display: 'block', marginBottom: '0.25rem' }}>Prescription Warnings</span>
            {activeFindings.prescription_warnings?.length > 0 ? (
              <ul style={{ paddingLeft: '1rem', margin: 0, fontSize: '0.85rem', color: '#fbbf24' }}>
                {activeFindings.prescription_warnings.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            ) : <p className="text-muted" style={{ fontSize: '0.85rem', margin: 0 }}>No prescription anomalies.</p>}
          </div>

          <hr style={{ border: '0', borderTop: '1px solid rgba(255,255,255,0.05)', margin: 0 }} />

          <div>
            <span style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 'bold', display: 'block', marginBottom: '0.25rem' }}>Smartwatch Observations</span>
            {activeFindings.wearable_observations?.length > 0 ? (
              <ul style={{ paddingLeft: '1rem', margin: 0, fontSize: '0.85rem', color: '#34d399' }}>
                {activeFindings.wearable_observations.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            ) : <p className="text-muted" style={{ fontSize: '0.85rem', margin: 0 }}>Smartwatch trends normal.</p>}
          </div>

          <hr style={{ border: '0', borderTop: '1px solid rgba(255,255,255,0.05)', margin: 0 }} />

          <div>
            <span style={{ fontSize: '0.8rem', color: '#8b5cf6', fontWeight: 'bold', display: 'block', marginBottom: '0.25rem' }}>Clinical Questions</span>
            {activeFindings.clinical_questions?.length > 0 ? (
              <ul style={{ paddingLeft: '1rem', margin: 0, fontSize: '0.85rem', color: '#a78bfa' }}>
                {activeFindings.clinical_questions.map((q, i) => <li key={i}>{q}</li>)}
              </ul>
            ) : <p className="text-muted" style={{ fontSize: '0.85rem', margin: 0 }}>No active inquiries.</p>}
          </div>

          <hr style={{ border: '0', borderTop: '1px solid rgba(255,255,255,0.05)', margin: 0 }} />

          <div>
            <span style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 'bold', display: 'block', marginBottom: '0.25rem' }}>Missing Evidence</span>
            {activeFindings.missing_evidence?.length > 0 ? (
              <ul style={{ paddingLeft: '1rem', margin: 0, fontSize: '0.85rem', color: '#7dd3fc' }}>
                {activeFindings.missing_evidence.map((me, i) => <li key={i}>{me}</li>)}
              </ul>
            ) : <p className="text-muted" style={{ fontSize: '0.85rem', margin: 0 }}>None detected.</p>}
          </div>

          <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="text-muted" style={{ fontSize: '0.75rem' }}>AI Confidence: {(activeFindings.confidence * 100).toFixed(0)}%</span>
            <button className="btn" style={{ padding: '0.3rem 0.8rem', fontSize: '0.8rem', border: '1px solid rgba(139, 92, 246, 0.5)', background: 'transparent' }}>
              Finalize Note
            </button>
          </div>

        </div>
      </div>

    </div>
  );
}

export default AiReviewTab;
