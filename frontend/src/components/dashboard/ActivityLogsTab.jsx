import { useState, useEffect } from 'react';

function ActivityLogsTab({ doctorCode }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await fetch(`http://${window.location.hostname}:5000/api/doctor/${doctorCode}/activity`);
      const result = await res.json();
      
      if (!res.ok || !result.success) {
        throw new Error(result.message || "Failed to fetch activity logs");
      }
      
      setLogs(result.data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [doctorCode]);

  if (loading) return <div className="text-center p-4">Loading activity logs...</div>;
  if (error) return <div className="text-center p-4" style={{color: 'var(--danger)'}}>Error: {error}</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3>Activity Logs</h3>
        <button className="btn" onClick={fetchLogs} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>Refresh</button>
      </div>

      {logs.length > 0 ? (
        <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.05)', borderBottom: '1px solid var(--glass-border)' }}>
                <th style={{ padding: '1rem' }}>Time</th>
                <th style={{ padding: '1rem' }}>Action</th>
                <th style={{ padding: '1rem' }}>Patient ID</th>
                <th style={{ padding: '1rem' }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, i) => (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '1rem' }}>{new Date(log.timestamp).toLocaleString()}</td>
                  <td style={{ padding: '1rem' }}>
                    <span style={{ 
                      background: 'rgba(139, 92, 246, 0.2)',
                      color: 'var(--secondary)',
                      padding: '0.25rem 0.75rem', 
                      borderRadius: '999px',
                      fontSize: '0.85rem'
                    }}>
                      {log.action}
                    </span>
                  </td>
                  <td style={{ padding: '1rem' }}>{log.patient_id || 'N/A'}</td>
                  <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p>No recent activity found.</p>
      )}
    </div>
  );
}

export default ActivityLogsTab;
