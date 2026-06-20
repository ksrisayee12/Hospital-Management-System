import { useState } from 'react';
import OverviewTab from './components/dashboard/OverviewTab';
import PatientsTab from './components/dashboard/PatientsTab';
import AppointmentsTab from './components/dashboard/AppointmentsTab';
import PrescribeTab from './components/dashboard/PrescribeTab';
import ActivityLogsTab from './components/dashboard/ActivityLogsTab';

function DoctorDashboard({ doctorCode }) {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'patients', label: 'Patients' },
    { id: 'appointments', label: 'Appointments' },
    { id: 'prescribe', label: 'Prescribe' },
    { id: 'logs', label: 'Activity Logs' }
  ];

  return (
    <div className="glass-panel" style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>Doctor Dashboard ({doctorCode})</h2>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`btn ${activeTab === tab.id ? '' : 'btn-danger'}`}
            style={{
              padding: '0.5rem 1rem',
              whiteSpace: 'nowrap',
              ...(activeTab !== tab.id ? { background: 'rgba(255,255,255,0.1)', color: 'var(--text-muted)' } : {})
            }}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="tab-content" style={{ minHeight: '400px' }}>
        {activeTab === 'overview' && <OverviewTab doctorCode={doctorCode} />}
        {activeTab === 'patients' && <PatientsTab doctorCode={doctorCode} />}
        {activeTab === 'appointments' && <AppointmentsTab doctorCode={doctorCode} />}
        {activeTab === 'prescribe' && <PrescribeTab doctorCode={doctorCode} />}
        {activeTab === 'logs' && <ActivityLogsTab doctorCode={doctorCode} />}
      </div>
    </div>
  );
}

export default DoctorDashboard;
