import React from 'react';

interface HeaderProps {
  title: string;
}

export const Header: React.FC<HeaderProps> = ({ title }) => {
  return (
    <header className="top-header">
      <div className="header-title">
        <span>⚙️</span>
        <span>{title}</span>
      </div>
      <div className="header-status">
        <div className="pulse-dot" title="Copilot Core Ready" />
        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>System Online</span>
      </div>
    </header>
  );
};
