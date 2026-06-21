/**
 * Mock data shaped to match Module 4's actual API response schemas
 * (see schemas/*.py in the backend). Swap each of these for a real
 * fetch() call once the backend is connected — the shapes are
 * intentionally identical so that swap is mechanical, not a rewrite.
 */

export const mockAlerts = [
  { alert_id: 'a1', user_id: 'DOC014', alert_type: 'EXCESSIVE_VIEWS', risk_score: 88, description: "Dr. Rao viewed the same MRI report 18 times in 90 minutes.", status: 'NEW', hospital_id: 'HOSP_A', created_at: '2026-06-21T08:12:00Z' },
  { alert_id: 'a2', user_id: 'DOC022', alert_type: 'OVERRIDE_ABUSE', risk_score: 76, description: "6 emergency overrides requested in the past 7 days.", status: 'UNDER_REVIEW', hospital_id: 'HOSP_A', created_at: '2026-06-20T19:40:00Z' },
  { alert_id: 'a3', user_id: 'DOC031', alert_type: 'ABNORMAL_DOWNLOAD', risk_score: 64, description: "17 reports downloaded within 5 minutes.", status: 'NEW', hospital_id: 'HOSP_B', created_at: '2026-06-20T14:02:00Z' },
  { alert_id: 'a4', user_id: 'DOC009', alert_type: 'REPEATED_ACCESS', risk_score: 41, description: "Unusual access pattern outside scheduled hours.", status: 'DISMISSED', hospital_id: 'HOSP_A', created_at: '2026-06-19T22:10:00Z' },
];

export const mockComplaints = [
  { complaint_id: 'c1', patient_id: 'PAT001', doctor_id: 'DOC014', category: 'UNAUTHORIZED_ACCESS', description: 'Doctor accessed my records without my consent during a routine visit.', status: 'OPEN', priority: 'HIGH', hospital_id: 'HOSP_A', created_at: '2026-06-21T07:30:00Z' },
  { complaint_id: 'c2', patient_id: 'PAT044', doctor_id: 'DOC022', category: 'MEDICAL_ERROR', description: 'Was prescribed the wrong dosage of medication.', status: 'UNDER_REVIEW', priority: 'CRITICAL', hospital_id: 'HOSP_A', created_at: '2026-06-20T11:00:00Z' },
  { complaint_id: 'c3', patient_id: 'PAT091', doctor_id: 'DOC005', category: 'BEHAVIORAL_ISSUE', description: 'Doctor was dismissive during a sensitive consultation.', status: 'RESOLVED', priority: 'LOW', hospital_id: 'HOSP_B', created_at: '2026-06-18T16:20:00Z' },
];

export const mockOverrides = [
  { request_id: 'e1', doctor_id: 'DOC022', patient_id: 'PAT077', reason: 'Emergency Surgery', urgency: 'CRITICAL', status: 'PENDING', hospital_id: 'HOSP_A', requested_at: '2026-06-21T08:50:00Z' },
  { request_id: 'e2', doctor_id: 'DOC014', patient_id: 'PAT012', reason: 'ICU Admission', urgency: 'HIGH', status: 'APPROVED', hospital_id: 'HOSP_A', requested_at: '2026-06-20T21:10:00Z' },
];

export const mockTrustScores = [
  { doctor_id: 'DOC014', name: 'Dr. Ananya Rao', role: 'Radiologist', hospital: 'Apollo Central', score: 62, risk_level: 'HIGH', delta: -8 },
  { doctor_id: 'DOC022', name: 'Dr. Vikram Mehta', role: 'Surgeon', hospital: 'Apollo Central', score: 71, risk_level: 'MODERATE', delta: -4 },
  { doctor_id: 'DOC031', name: 'Dr. Sara Thomas', role: 'General Physician', hospital: 'Fortis North', score: 84, risk_level: 'LOW', delta: -1 },
  { doctor_id: 'DOC005', name: 'Dr. Kabir Singh', role: 'Cardiologist', hospital: 'Fortis North', score: 96, risk_level: 'LOW', delta: 0 },
  { doctor_id: 'DOC009', name: 'Dr. Priya Nair', role: 'Pediatrician', hospital: 'Apollo Central', score: 100, risk_level: 'LOW', delta: 0 },
];

export const mockHospitals = [
  { hospital_id: 'HOSP_A', hospital_name: 'Apollo Central', risk_score: 64, avg_trust_score: 79, open_complaints: 2, active_alerts: 3, total_overrides: 5 },
  { hospital_id: 'HOSP_B', hospital_name: 'Fortis North', risk_score: 22, avg_trust_score: 91, open_complaints: 0, active_alerts: 1, total_overrides: 1 },
  { hospital_id: 'HOSP_C', hospital_name: 'Manipal East', risk_score: 38, avg_trust_score: 88, open_complaints: 1, active_alerts: 1, total_overrides: 2 },
];

export const mockLedgerEvents = [
  { event_id: 'l1', sequence_number: 142, event_type: 'CONSENT_APPROVED', current_hash: '8f3a1c9e2b7d4f6a0e1c5b8d3f7a9e2c4b6d8f1a3c5e7b9d1f3a5c7e9b1d3f5a', previous_hash: '3a5c7e9b1d3f5a8f3a1c9e2b7d4f6a0e1c5b8d3f7a9e2c4b6d8f1a3c5e7b9d1f', timestamp: '2026-06-21T08:55:00Z', summary: 'Patient PAT001 approved consent for Dr. Rao.' },
  { event_id: 'l2', sequence_number: 141, event_type: 'EMERGENCY_OVERRIDE_APPROVED', current_hash: '3a5c7e9b1d3f5a8f3a1c9e2b7d4f6a0e1c5b8d3f7a9e2c4b6d8f1a3c5e7b9d1f', previous_hash: '1c5b8d3f7a9e2c4b6d8f1a3c5e7b9d1f3a5c7e9b1d3f5a8f3a1c9e2b7d4f6a0e', timestamp: '2026-06-20T21:12:00Z', summary: 'Admin approved emergency access for Dr. Mehta on PAT012.' },
  { event_id: 'l3', sequence_number: 140, event_type: 'COMPLAINT_CREATED', current_hash: '1c5b8d3f7a9e2c4b6d8f1a3c5e7b9d1f3a5c7e9b1d3f5a8f3a1c9e2b7d4f6a0e', previous_hash: '6d8f1a3c5e7b9d1f3a5c7e9b1d3f5a8f3a1c9e2b7d4f6a0e1c5b8d3f7a9e2c4b', timestamp: '2026-06-20T11:01:00Z', summary: 'PAT044 filed a complaint against Dr. Mehta.' },
  { event_id: 'l4', sequence_number: 139, event_type: 'PRESCRIPTION_SIGNED', current_hash: '6d8f1a3c5e7b9d1f3a5c7e9b1d3f5a8f3a1c9e2b7d4f6a0e1c5b8d3f7a9e2c4b', previous_hash: '9e2c4b6d8f1a3c5e7b9d1f3a5c7e9b1d3f5a8f3a1c9e2b7d4f6a0e1c5b8d3f7a', timestamp: '2026-06-19T15:40:00Z', summary: 'Dr. Thomas digitally signed a prescription for PAT091.' },
];

export const platformMetrics = {
  platformRiskScore: { value: 41, delta: -3 },
  trustScore: { value: 84, delta: -2 },
  openAlerts: { value: 7, delta: 12 },
  activeCases: { value: 4, delta: 0 },
};

export const trendSeries = {
  risk: [38, 40, 39, 44, 41, 43, 41].map((v) => ({ value: v })),
  trust: [88, 87, 86, 85, 85, 84, 84].map((v) => ({ value: v })),
};

export const recentActivity = [
  { id: 'r1', title: 'Dr. Rao flagged for excessive viewing', description: 'AI Security Engine raised an EXCESSIVE_VIEWS alert.', timestamp: '12m ago', tone: 'danger' },
  { id: 'r2', title: 'Emergency override approved', description: 'Admin approved 24h access for Dr. Mehta on PAT012.', timestamp: '1h ago', tone: 'success' },
  { id: 'r3', title: 'New complaint filed', description: 'PAT044 filed a MEDICAL_ERROR complaint.', timestamp: '3h ago', tone: 'warning' },
  { id: 'r4', title: 'Consent approved', description: 'PAT001 approved consent for Dr. Rao.', timestamp: '5h ago', tone: 'info' },
];
