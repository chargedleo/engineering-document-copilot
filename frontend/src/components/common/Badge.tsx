import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: string; // Kept for API compatibility, rendered monochrome
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, className = '' }) => {
  return (
    <span
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '0.15rem 0.45rem',
        fontSize: '0.72rem',
        fontFamily: 'var(--font-mono)',
        fontWeight: 600,
        letterSpacing: '0.04em',
        textTransform: 'uppercase',
        border: '1px solid var(--border-subtle)',
        color: 'var(--text-primary)',
        backgroundColor: 'var(--surface-subtle)',
        borderRadius: 0,
      }}
    >
      {children}
    </span>
  );
};
