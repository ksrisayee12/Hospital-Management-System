import { useState, useEffect } from 'react';

function OverviewTab({ doctorCode }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await fetch(`http://${window.location.hostname}:5000/api/doctor/${doctorCode}/dashboard`);
      const result = await res.json();
      
      if (!res.ok || !result.success) {
        throw new Error(result.message || "Failed to fetch dashboard");
      }
      
      setData(result.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [doctorCode]);

  if (loading) return <div className="text-center p-4">Loading overview data...</div>;
  if (error) return <div className="text-center p-4" style={{color: 'var(--danger)'}}>Error: {error}</div>;
  if (!data) return null;

  return (
    <div>
      <div className="grid-container" style={{ marginTop: '1rem', marginBottom: '2rem' }}>
        <div className="glass-panel" style={{ padding: '1.5rem', background: 'rgba(59, 130, 246, 0.1)' }}>
          <h3>Total Patients</h3>
          <p style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--primary)' }}>{data.total_patients}</p>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem', background: 'rgba(139, 92, 246, 0.1)' }}>
          <h3>Appointments</h3>
          <p style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--secondary)' }}>{data.total_appointments}</p>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem', background: 'rgba(16, 185, 129, 0.1)' }}>
          <h3>Activity Logs</h3>
          <p style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--accent)' }}>{data.total_activities}</p>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem', background: 'rgba(245, 158, 11, 0.1)' }}>
          <h3>NFC Access Count</h3>
          <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b' }}>{data.access_count}</p>
        </div>
      </div>

      <div className="flex justify-between items-center mb-4">
        <h3>Recent Appointments</h3>
        <button className="btn" onClick={fetchDashboard} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>Refresh</button>
      </div>

      {data.appointments && data.appointments.length > 0 ? (
        <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.05)', borderBottom: '1px solid var(--glass-border)' }}>
                <th style={{ padding: '1rem' }}>Patient ID</th>
                <th style={{ padding: '1rem' }}>Time</th>
                <th style={{ padding: '1rem' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.appointments.slice(0, 5).map((apt, i) => (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '1rem' }}>{apt.patient_id}</td>
                  <td style={{ padding: '1rem' }}>{new Date(apt.appointment_time).toLocaleString()}</td>
                  <td style={{ padding: '1rem' }}>
                    <span style={{ 
                      background: apt.status === 'COMPLETED' ? 'rgba(16,185,129,0.2)' : 'rgba(59,130,246,0.2)',
                      color: apt.status === 'COMPLETED' ? 'var(--accent)' : 'var(--primary)',
                      padding: '0.25rem 0.75rem', 
                      borderRadius: '999px',
                      fontSize: '0.85rem'
                    }}>
                      {apt.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p>No recent appointments found.</p>
      )}
    </div>
  );
}

export default OverviewTab;
