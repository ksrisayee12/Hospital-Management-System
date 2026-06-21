import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';

export default function DevLogin() {
  const [show, setShow] = useState(false);
  const [role, setRole] = useState('super_admin');
  const [sub, setSub] = useState('00000000-0000-0000-0000-000000000001');

  useEffect(() => {
    if (!localStorage.getItem('dev_token')) {
      setShow(true);
    }
  }, []);

  const handleLogin = async () => {
    try {
      const res = await api.post('/dev/token', { sub, role, hospital_id: 'HOSP-123' });
      localStorage.setItem('dev_token', res.access_token);
      setShow(false);
      window.location.reload(); 
    } catch (err) {
      alert('Login failed: ' + err);
    }
  };

  const logout = () => {
    localStorage.removeItem('dev_token');
    setShow(true);
  };

  if (!show) {
    return (
      <button 
        onClick={logout}
        style={{
          position: 'fixed', bottom: 16, right: 16, zIndex: 9999,
          background: 'var(--color-card, #1e1e1e)', color: 'var(--color-text-secondary, #a0a0a0)',
          border: '1px solid var(--color-border, #333)', padding: '6px 12px',
          borderRadius: 4, fontSize: 12, cursor: 'pointer'
        }}
      >
        Logout / Dev Options
      </button>
    );
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10000
    }}>
      <div style={{
        background: 'var(--color-background, #121212)', border: '1px solid var(--color-border, #333)',
        padding: 24, borderRadius: 8, width: 360, display: 'flex', flexDirection: 'column', gap: 16,
        color: 'var(--color-text-primary, #fff)', fontFamily: 'inherit'
      }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>Dev Login (Module 1 Bypass)</h2>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 12, color: 'var(--color-text-muted, #777)' }}>Role</label>
          <select 
            style={{
              background: 'var(--color-card, #1e1e1e)', color: '#fff', border: '1px solid var(--color-border, #333)',
              padding: 8, borderRadius: 4, outline: 'none', fontSize: 14
            }}
            value={role} onChange={e => setRole(e.target.value)}
          >
            <option value="super_admin">super_admin (Full Access)</option>
            <option value="admin">admin (Hospital Access)</option>
            <option value="doctor">doctor (Limited)</option>
            <option value="patient">patient (Submit only)</option>
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 12, color: 'var(--color-text-muted, #777)' }}>User UUID (sub)</label>
          <input 
            style={{
              background: 'var(--color-card, #1e1e1e)', color: '#fff', border: '1px solid var(--color-border, #333)',
              padding: 8, borderRadius: 4, outline: 'none', fontSize: 14
            }}
            value={sub} onChange={e => setSub(e.target.value)}
          />
        </div>

        <button 
          onClick={handleLogin}
          style={{
            background: 'var(--color-primary, #2563EB)', color: '#fff', border: 'none',
            padding: 10, borderRadius: 4, fontWeight: 600, cursor: 'pointer', marginTop: 8
          }}
        >
          Generate JWT & Login
        </button>
      </div>
    </div>
  );
}
