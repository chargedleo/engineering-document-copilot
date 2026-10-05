import React, { useState } from 'react';
import { Header, ActiveTab } from './Header';

interface MainLayoutProps {
  children: (activeTab: ActiveTab) => React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('chat');

  return (
    <div className="app-shell">
      <Header activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="main-viewport">
        {children(activeTab)}
      </main>
      <footer className="footer-bar">
        <div className="footer-inner">
          <div className="footer-copy">
            Engineering Document Intelligence & CAD Knowledge Copilot
          </div>
          <div className="footer-links">
            <a
              href="file:///d:/Projects/Engineering%20copilot/README.md"
              className="footer-link"
              target="_blank"
              rel="noreferrer"
            >
              Documentation
            </a>
            <button
              className="footer-link"
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              onClick={() => setActiveTab('architecture')}
            >
              Architecture
            </button>
            <a
              href="http://localhost:8000/docs"
              className="footer-link"
              target="_blank"
              rel="noreferrer"
            >
              API Reference
            </a>
            <a
              href="https://github.com"
              className="footer-link"
              target="_blank"
              rel="noreferrer"
            >
              GitHub
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};
