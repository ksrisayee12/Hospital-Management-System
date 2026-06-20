import { useState } from 'react';

function PrescribeTab({ doctorCode }) {
  const [formData, setFormData] = useState({
    patient_id: '',
    medicine_name: '',
    dosage: '',
    frequency: '',
    duration: '',
    allergies: ''
  });
  const [validationResult, setValidationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    // Reset validation when form changes
    setValidationResult(null);
    setSuccessMsg(null);
  };

  const validatePrescription = async (e) => {
    e.preventDefault();
    if (!formData.medicine_name || !formData.dosage) {
      alert("Medicine name and dosage are required for validation");
      return;
    }

    try {
      setLoading(true);
      const allergiesList = formData.allergies ? formData.allergies.split(',').map(a => a.trim()) : [];
      
      const res = await fetch(`http://${window.location.hostname}:5000/api/clinical/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          medicine_name: formData.medicine_name,
          dosage: formData.dosage,
          allergies: allergiesList
        })
      });
      const result = await res.json();
      
      if (!res.ok || !result.success) {
        throw new Error(result.message || "Validation failed");
      }
      
      setValidationResult(result.data);
    } catch (err) {
      alert("Validation Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const submitPrescription = async () => {
    try {
      setSubmitting(true);
      const payload = {
        ...formData,
        doctor_code: doctorCode,
        doctor_confirmed: true
      };

      const res = await fetch(`http://${window.location.hostname}:5000/api/prescription/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const result = await res.json();
      
      if (!res.ok || !result.success) {
        throw new Error(result.message || "Failed to create prescription");
      }
      
      setSuccessMsg("Prescription created successfully!");
      setFormData({
        patient_id: '',
        medicine_name: '',
        dosage: '',
        frequency: '',
        duration: '',
        allergies: ''
      });
      setValidationResult(null);
    } catch (err) {
      alert("Submission Error: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <h3>New Prescription</h3>
      <p style={{ marginBottom: '1.5rem' }}>Create a new prescription with AI clinical validation.</p>

      {successMsg && (
        <div style={{ background: 'rgba(16, 185, 129, 0.2)', color: 'var(--accent)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
          {successMsg}
        </div>
      )}

      <form onSubmit={validatePrescription}>
        <div className="grid-container" style={{ marginTop: 0, gap: '1rem', gridTemplateColumns: '1fr 1fr' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Patient ID</label>
            <input name="patient_id" value={formData.patient_id} onChange={handleChange} placeholder="e.g. PAT001" required />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Patient Allergies (comma separated)</label>
            <input name="allergies" value={formData.allergies} onChange={handleChange} placeholder="e.g. penicillin, peanuts" />
          </div>
        </div>

        <div className="grid-container" style={{ marginTop: 0, gap: '1rem', gridTemplateColumns: '1fr 1fr' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Medicine Name</label>
            <input name="medicine_name" value={formData.medicine_name} onChange={handleChange} placeholder="e.g. Amoxicillin" required />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Dosage</label>
            <input name="dosage" value={formData.dosage} onChange={handleChange} placeholder="e.g. 500mg" required />
          </div>
        </div>

        <div className="grid-container" style={{ marginTop: 0, gap: '1rem', gridTemplateColumns: '1fr 1fr' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Frequency</label>
            <input name="frequency" value={formData.frequency} onChange={handleChange} placeholder="e.g. Twice a day" required />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Duration</label>
            <input name="duration" value={formData.duration} onChange={handleChange} placeholder="e.g. 7 days" required />
          </div>
        </div>

        {!validationResult ? (
          <button type="submit" className="btn" style={{ width: '100%', marginTop: '1rem' }} disabled={loading}>
            {loading ? 'Validating...' : 'Validate Prescription with AI'}
          </button>
        ) : null}
      </form>

      {validationResult && (
        <div className="glass-panel" style={{ marginTop: '2rem', padding: '1.5rem', background: validationResult.ai_status === 'CRITICAL' ? 'rgba(239, 68, 68, 0.1)' : validationResult.ai_status === 'WARNING' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(16, 185, 129, 0.1)' }}>
          <h4>AI Validation Status: 
            <span style={{ 
              marginLeft: '0.5rem',
              color: validationResult.ai_status === 'CRITICAL' ? 'var(--danger)' : validationResult.ai_status === 'WARNING' ? '#f59e0b' : 'var(--accent)'
            }}>
              {validationResult.ai_status}
            </span>
          </h4>
          
          {validationResult.alerts && validationResult.alerts.length > 0 && (
            <ul style={{ marginTop: '1rem', color: 'var(--danger)', paddingLeft: '1.5rem' }}>
              {validationResult.alerts.map((alert, idx) => (
                <li key={idx} style={{ marginBottom: '0.5rem' }}>{alert}</li>
              ))}
            </ul>
          )}
          
          <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
            <button className="btn" style={{ flex: 1 }} onClick={submitPrescription} disabled={submitting}>
              {submitting ? 'Submitting...' : 'Confirm & Prescribe'}
            </button>
            <button className="btn btn-danger" style={{ flex: 1 }} onClick={() => setValidationResult(null)}>
              Cancel / Edit
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default PrescribeTab;
