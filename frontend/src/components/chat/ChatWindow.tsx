import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../../hooks/useChat';
import { Badge } from '../common/Badge';

export const ChatWindow: React.FC = () => {
  const { messages, loading, error, sendMessage } = useChat();
  const [inputQuery, setInputQuery] = useState('');
  const [includeCad, setIncludeCad] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || loading) return;
    sendMessage(inputQuery, includeCad);
    setInputQuery('');
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', margin: 'auto', maxWidth: '520px', color: 'var(--text-secondary)' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🤖</div>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              Engineering Document Intelligence & CAD Copilot
            </h3>
            <p style={{ fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Ask questions about technical specifications, material tolerances, compliance standards, or CAD assembly properties.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <button
                className="btn btn-secondary"
                style={{ textAlign: 'left', fontSize: '0.85rem' }}
                onClick={() => sendMessage('What are the maximum operating temperature limits for the turbine blade?', true)}
              >
                💡 "What are the maximum operating temperature limits for the turbine blade?"
              </button>
              <button
                className="btn btn-secondary"
                style={{ textAlign: 'left', fontSize: '0.85rem' }}
                onClick={() => sendMessage('Verify tolerance compatibility for shaft assembly part TS-402-C.', true)}
              >
                💡 "Verify tolerance compatibility for shaft assembly part TS-402-C."
              </button>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`chat-bubble ${msg.role}`}>
            <div style={{ fontWeight: 600, fontSize: '0.8rem', marginBottom: '0.25rem', opacity: 0.8 }}>
              {msg.role === 'user' ? 'Engineering Query' : 'Copilot Intelligence'}
            </div>
            <div>{msg.content}</div>

            {/* Render Citations if assistant message */}
            {msg.citations && msg.citations.length > 0 && (
              <div style={{ marginTop: '0.75rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-primary)' }}>
                  Grounded Citations:
                </span>
                {msg.citations.map((cite, index) => (
                  <div key={index} className="citation-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
                      <span style={{ fontWeight: 600 }}>{cite.document_title}</span>
                      <span style={{ fontSize: '0.7rem' }}>{cite.section || `Page ${cite.page_number}`}</span>
                    </div>
                    <p style={{ fontStyle: 'italic', margin: 0 }}>"{cite.snippet}"</p>
                  </div>
                ))}
              </div>
            )}

            {/* Render CAD References */}
            {msg.cad_references && msg.cad_references.length > 0 && (
              <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {msg.cad_references.map((cad, idx) => (
                  <Badge key={idx} variant="info">
                    CAD: {cad.part_number} ({cad.part_name || 'Part'})
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="chat-bubble assistant" style={{ opacity: 0.7 }}>
            <span style={{ fontStyle: 'italic' }}>Analyzing specifications and CAD geometry...</span>
          </div>
        )}

        {error && (
          <div style={{ color: 'var(--danger)', fontSize: '0.85rem', padding: '0.5rem' }}>
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input-bar">
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={includeCad}
            onChange={(e) => setIncludeCad(e.target.checked)}
          />
          Include CAD Context
        </label>
        <input
          type="text"
          className="chat-input"
          placeholder="Ask an engineering question or cross-reference CAD specs..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !inputQuery.trim()}>
          <span>Send</span>
        </button>
      </form>
    </div>
  );
};
