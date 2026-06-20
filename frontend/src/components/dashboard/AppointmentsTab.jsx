import { useState, useEffect } from 'react';

function AppointmentsTab({ doctorCode }) {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      const res = await fetch(`http://${window.location.hostname}:5000/api/appointments/${doctorCode}`);
      const result = await res.json();
      
      if (!res.ok || !result.success) {
        throw new Error(result.message || "Failed to fetch appointments");
      }
      
      setAppointments(result.data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (id, newStatus) => {
    try {
      const res = await fetch(`http://${window.location.hostname}:5000/api/appointments/update-status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ appointment_id: id, status: newStatus })
      });
      const result = await res.json();
      
      if (!res.ok || !result.success) {
        throw new Error(result.message || "Failed to update status");
      }
      
      fetchAppointments();
    } catch (err) {
      alert("Error updating status: " + err.message);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, [doctorCode]);

  if (loading) return <div className="text-center p-4">Loading appointments...</div>;
  if (error) return <div className="text-center p-4" style={{color: 'var(--danger)'}}>Error: {error}</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3>All Appointments</h3>
        <button className="btn" onClick={fetchAppointments} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>Refresh</button>
      </div>

      {appointments.length > 0 ? (
        <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.05)', borderBottom: '1px solid var(--glass-border)' }}>
                <th style={{ padding: '1rem' }}>Patient ID</th>
                <th style={{ padding: '1rem' }}>Time</th>
                <th style={{ padding: '1rem' }}>Status</th>
                <th style={{ padding: '1rem' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((apt, i) => (
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
                  <td style={{ padding: '1rem' }}>
                    {apt.status !== 'COMPLETED' && (
                      <button 
                        className="btn" 
                        style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem' }}
                        onClick={() => updateStatus(apt.id, 'COMPLETED')}
                      >
                        Mark Completed
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p>No appointments scheduled.</p>
      )}
    </div>
  );
}

export default AppointmentsTab;
