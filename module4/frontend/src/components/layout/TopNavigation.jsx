import React, { useState } from 'react';
import { SearchCommand } from '../primitives';

const NAV_ITEMS = [
  { key: 'command-center',    label: 'Command Center' },
  { key: 'investigations',    label: 'Investigations' },
  { key: 'trust-risk',        label: 'Trust & Risk' },
  { key: 'governance-ledger', label: 'Governance Ledger' },
  { key: 'network-analytics', label: 'Network Analytics' },
];

/**
 * TopNavigation
 *
 * Deliberately no sidebar — per brief, this should feel like
 * workflows, not a page tree. Active item gets an underline, not a
 * filled pill, to keep the bar visually quiet.
 *
 * On mobile (≤768px): nav collapses into a hamburger menu.
 */
export default function TopNavigation({ active, onNavigate, userName = 'Admin', userRole = 'Hospital Admin' }) {
  const [menuOpen, setMenuOpen] = useState(false);

  function handleNav(key) {
    onNavigate(key);
    setMenuOpen(false);
  }

  return (
    <>
      <header
        style={{
          height: 'var(--topnav-height)',
          borderBottom: '1px solid var(--color-border)',
          background: 'var(--color-card)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-6)',
          padding: '0 var(--space-6)',
          position: 'sticky',
          top: 0,
          zIndex: 10,
        }}
      >
        {/* Logo mark */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexShrink: 0 }}>
          <div
            style={{
              width: 26,
              height: 26,
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldIcon />
          </div>
          <span style={{ fontWeight: 650, fontSize: 'var(--text-base)', color: 'var(--color-text-primary)' }}>
            Governance
          </span>
        </div>

        {/* Desktop nav */}
        <nav className="topnav-desktop" style={{ display: 'flex', gap: 'var(--space-5)', flex: 1 }}>
          {NAV_ITEMS.map((item) => {
            const isActive = item.key === active;
            return (
              <button
                key={item.key}
                onClick={() => handleNav(item.key)}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: '0',
                  height: 'var(--topnav-height)',
                  fontSize: 'var(--text-sm)',
                  fontWeight: isActive ? 650 : 500,
                  color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                  borderBottom: isActive ? '2px solid var(--color-primary)' : '2px solid transparent',
                  cursor: 'pointer',
                  transition: 'color var(--duration-fast) var(--ease-out)',
                  whiteSpace: 'nowrap',
                }}
                onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.color = 'var(--color-text-primary)'; }}
                onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.color = 'var(--color-text-secondary)'; }}
              >
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Search — hidden on very small screens */}
        <div className="topnav-search">
          <SearchCommand />
        </div>

        {/* User avatar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexShrink: 0 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              background: 'var(--color-purple-soft)',
              color: 'var(--color-purple)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 'var(--text-sm)',
              fontWeight: 650,
              flexShrink: 0,
            }}
          >
            {userName.charAt(0)}
          </div>
          <div className="topnav-user-info" style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
            <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              {userName}
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>{userRole}</span>
          </div>
        </div>

        {/* Hamburger — mobile only */}
        <button
          className="topnav-hamburger"
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="Toggle navigation menu"
          aria-expanded={menuOpen}
          style={{
            display: 'none',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 'var(--space-2)',
            color: 'var(--color-text-primary)',
            flexShrink: 0,
          }}
        >
          <HamburgerIcon open={menuOpen} />
        </button>
      </header>

      {/* Mobile dropdown menu */}
      {menuOpen && (
        <div
          className="topnav-mobile-menu"
          style={{
            position: 'fixed',
            top: 'var(--topnav-height)',
            left: 0,
            right: 0,
            background: 'var(--color-card)',
            borderBottom: '1px solid var(--color-border)',
            zIndex: 9,
            padding: 'var(--space-2) 0',
            boxShadow: 'var(--shadow-md)',
          }}
        >
          {NAV_ITEMS.map((item) => {
            const isActive = item.key === active;
            return (
              <button
                key={item.key}
                onClick={() => handleNav(item.key)}
                style={{
                  display: 'block',
                  width: '100%',
                  textAlign: 'left',
                  background: isActive ? 'var(--color-primary-soft)' : 'none',
                  border: 'none',
                  padding: 'var(--space-3) var(--space-6)',
                  fontSize: 'var(--text-base)',
                  fontWeight: isActive ? 650 : 500,
                  color: isActive ? 'var(--color-primary)' : 'var(--color-text-primary)',
                  cursor: 'pointer',
                }}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .topnav-desktop { display: none !important; }
          .topnav-search  { display: none !important; }
          .topnav-user-info { display: none !important; }
          .topnav-hamburger { display: flex !important; }
        }
      `}</style>
    </>
  );
}

function ShieldIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2">
      <path d="M12 2 4 6v6c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V6l-8-4Z" />
    </svg>
  );
}

function HamburgerIcon({ open }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      {open ? (
        <>
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </>
      ) : (
        <>
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </>
      )}
    </svg>
  );
}
