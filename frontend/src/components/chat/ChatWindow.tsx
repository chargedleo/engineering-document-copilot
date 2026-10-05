import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../../hooks/useChat';
import { AgentCitation, ToolExecutionTrace } from '../../types';

export const ChatWindow: React.FC = () => {
  const { turns, loading, error, sendQuery } = useChat();
  const [inputQuery, setInputQuery] = useState('');
  const [partNumberFilter, setPartNumberFilter] = useState('');
  const [revisionFilter, setRevisionFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});

  const streamEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    streamEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [turns, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || loading) return;

    const filters = (partNumberFilter.trim() || revisionFilter.trim())
      ? {
          part_number: partNumberFilter.trim() || undefined,
          revision: revisionFilter.trim() || undefined,
        }
      : undefined;

    sendQuery(inputQuery, filters);
    setInputQuery('');
  };

  const toggleCitationSnippet = (citationKey: string) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [citationKey]: !prev[citationKey],
    }));
  };

  // Helper to extract calculation trace if present
  const getCalculationTrace = (traces: ToolExecutionTrace[] = []) => {
    return traces.find(
      (t) => t.tool_name === 'calculate_engineering' && t.status === 'success' && t.output_summary
    );
  };

  return (
    <div style={{ maxWidth: 'var(--max-width-editorial)', margin: '0 auto' }}>
      {/* Empty State / Editorial Hero */}
      {turns.length === 0 && (
        <section className="hero-editorial">
          <div className="hero-kicker">Technical Intelligence</div>
          <h1 className="hero-title">Engineering Copilot</h1>
          <p className="hero-description">
            Search technical documentation, retrieve verified engineering facts,
            and perform constrained engineering calculations.
          </p>

          <div className="starters-section">
            <div className="starters-label">Verified Specification Queries</div>
            <div className="starters-list">
              <button
                type="button"
                className="starter-item"
                onClick={() =>
                  sendQuery('What is the maximum working pressure of CFP-402-316L in psi?')
                }
              >
                <span>What is the maximum working pressure of CFP-402-316L in psi?</span>
                <span className="starter-arrow">→</span>
              </button>

              <button
                type="button"
                className="starter-item"
                onClick={() =>
                  sendQuery('What is the radial bearing journal tolerance?')
                }
              >
                <span>What is the radial bearing journal tolerance?</span>
                <span className="starter-arrow">→</span>
              </button>

              <button
                type="button"
                className="starter-item"
                onClick={() =>
                  sendQuery('What is the document revision and status for sample_pump_spec.pdf?')
                }
              >
                <span>What is the document revision and status for sample_pump_spec.pdf?</span>
                <span className="starter-arrow">→</span>
              </button>

              <button
                type="button"
                className="starter-item"
                onClick={() =>
                  sendQuery('Convert 75 kW to horsepower')
                }
              >
                <span>Convert 75 kW to horsepower</span>
                <span className="starter-arrow">→</span>
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Conversation Stream (Editorial Document Layout) */}
      {turns.length > 0 && (
        <div className="conversation-stream">
          {turns.map((turn, index) => {
            const calcTrace = turn.response ? getCalculationTrace(turn.response.tool_traces) : undefined;
            const calcOutput = calcTrace?.output_summary;

            return (
              <article key={turn.id} className="conversation-turn">
                {/* 1. User Query Block */}
                <div className="user-query-block">
                  <span className="section-label">User Query · {String(index + 1).padStart(2, '0')}</span>
                  <h2 className="user-query-text">{turn.query}</h2>
                </div>

                <hr className="editorial-divider" />

                {/* 2. Loading State */}
                {turn.loading && (
                  <div className="loading-indicator pulse-monochrome">
                    <span>●</span>
                    <span>Reasoning across engineering sources and executing tools...</span>
                  </div>
                )}

                {/* 3. Error State */}
                {turn.error && (
                  <div className="abstention-notice">
                    <span className="abstention-heading">Execution Notice</span>
                    <p className="abstention-body">{turn.error}</p>
                  </div>
                )}

                {/* 4. Copilot Response Block */}
                {turn.response && (
                  <div className="copilot-response-block">
                    <span className="section-label">Engineering Copilot</span>

                    {/* Abstention State vs Grounded Synthesis */}
                    {turn.response.should_abstain ? (
                      <div className="abstention-notice">
                        <span className="abstention-heading">Insufficient Evidence</span>
                        <p className="abstention-body">{turn.response.answer}</p>
                      </div>
                    ) : (
                      <div className="copilot-answer-text">{turn.response.answer}</div>
                    )}

                    {/* Typographic Calculation Sheet */}
                    {calcOutput && (
                      <div className="calculation-sheet">
                        <span className="calculation-header">Calculated Value</span>
                        <div className="calculation-result">
                          {calcOutput.result} {calcOutput.unit}
                        </div>
                        <div className="calculation-formula">
                          {calcOutput.explanation || `${calcOutput.input} → ${calcOutput.result} ${calcOutput.unit}`}
                        </div>
                        {calcOutput.input && (
                          <div className="calculation-source">
                            Source Value: {calcOutput.input} {calcOutput.operation?.split('_')[0] || ''} [C1]
                          </div>
                        )}
                      </div>
                    )}

                    {/* Sources (Bordered Technical References) */}
                    {turn.response.citations && turn.response.citations.length > 0 && (
                      <div className="sources-section">
                        <span className="section-label">
                          Sources ({turn.response.citations.length} Verified References)
                        </span>
                        <div className="sources-list">
                          {turn.response.citations.map((cite: AgentCitation, cIdx: number) => {
                            const cKey = `${turn.id}-${cite.citation_id}-${cIdx}`;
                            const isExpanded = !!expandedCitations[cKey];

                            return (
                              <div key={cKey} className="source-item">
                                <div className="source-header">
                                  <span className="source-tag">[{cite.citation_id}]</span>
                                  <span className="source-filename">{cite.filename}</span>
                                  <span className="source-meta">
                                    Page {cite.page_number}
                                    {cite.revision ? ` · Revision ${cite.revision}` : ''}
                                    {cite.chunk_index !== undefined && cite.chunk_index !== null ? ` · Chunk #${cite.chunk_index}` : ''}
                                    {cite.part_number ? ` · Part: ${cite.part_number}` : ''}
                                  </span>
                                </div>

                                {cite.section && (
                                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                    Section: {cite.section}
                                  </div>
                                )}

                                {cite.snippet && (
                                  <div>
                                    <button
                                      type="button"
                                      className="text-link"
                                      style={{
                                        fontSize: '0.75rem',
                                        background: 'none',
                                        border: 'none',
                                        cursor: 'pointer',
                                        padding: 0,
                                        marginTop: '0.2rem',
                                      }}
                                      onClick={() => toggleCitationSnippet(cKey)}
                                    >
                                      {isExpanded ? 'Hide Excerpt' : 'View Excerpt'}
                                    </button>
                                    {isExpanded && (
                                      <div className="source-snippet">{cite.snippet}</div>
                                    )}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Tool Activity Log (Compact Technical Log) */}
                    {turn.response.tool_traces && turn.response.tool_traces.length > 0 && (
                      <div className="tool-activity-section">
                        <span className="section-label">Tool Activity</span>
                        <div className="tool-log-table">
                          {turn.response.tool_traces.map((trace, tIdx) => (
                            <div key={tIdx} className="tool-log-row">
                              <span className="tool-log-index">
                                {String(tIdx + 1).padStart(2, '0')}
                              </span>
                              <span className="tool-log-status">
                                {trace.status === 'success' ? '[OK]' : '[ERR]'}
                              </span>
                              <span className="tool-log-name">{trace.tool_name}</span>
                              <span className="tool-log-detail">
                                {trace.tool_name === 'search_engineering_documents' && trace.output_summary
                                  ? `${trace.output_summary.hits_count || 0} hits · ${trace.output_summary.retrieval_mode || 'hybrid'}`
                                  : trace.tool_name === 'calculate_engineering' && trace.output_summary
                                  ? `${trace.output_summary.operation}: ${trace.output_summary.input} → ${trace.output_summary.result} ${trace.output_summary.unit}`
                                  : trace.tool_name === 'get_document_metadata' && trace.output_summary
                                  ? `Rev ${trace.output_summary.revision || '-'} · ${trace.output_summary.status || 'OK'}`
                                  : trace.status}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Provenance Metadata */}
                    {turn.response.metadata && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        Provider: {turn.response.metadata.provider || 'local_mock'}
                        {turn.response.metadata.model ? ` (${turn.response.metadata.model})` : ''}
                        {turn.response.metadata.latency_ms ? ` · Latency: ${turn.response.metadata.latency_ms.toFixed(1)} ms` : ''}
                      </div>
                    )}
                  </div>
                )}
              </article>
            );
          })}
          <div ref={streamEndRef} />
        </div>
      )}

      {/* Sticky Input Dock */}
      <div className="input-dock">
        {showFilters && (
          <div
            style={{
              display: 'flex',
              gap: '0.75rem',
              marginBottom: '0.75rem',
              padding: '0.75rem',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--surface-subtle)',
            }}
          >
            <div style={{ flex: 1 }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  color: 'var(--text-muted)',
                  marginBottom: '0.25rem',
                }}
              >
                Part Number Filter
              </label>
              <input
                type="text"
                placeholder="e.g. CFP-402-316L"
                value={partNumberFilter}
                onChange={(e) => setPartNumberFilter(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.4rem 0.6rem',
                  fontSize: '0.85rem',
                  border: '1px solid var(--border-medium)',
                  backgroundColor: 'var(--canvas-bg)',
                  fontFamily: 'var(--font-mono)',
                }}
              />
            </div>
            <div style={{ width: '120px' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  color: 'var(--text-muted)',
                  marginBottom: '0.25rem',
                }}
              >
                Revision
              </label>
              <input
                type="text"
                placeholder="e.g. D"
                value={revisionFilter}
                onChange={(e) => setRevisionFilter(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.4rem 0.6rem',
                  fontSize: '0.85rem',
                  border: '1px solid var(--border-medium)',
                  backgroundColor: 'var(--canvas-bg)',
                  fontFamily: 'var(--font-mono)',
                }}
              />
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            className="text-input"
            placeholder="Search engineering documentation, specifications, tolerances..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !inputQuery.trim()}
          >
            Ask Engineering Copilot
          </button>
        </form>

        <div style={{ marginTop: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            type="button"
            className="text-link"
            style={{ fontSize: '0.75rem', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
            onClick={() => setShowFilters(!showFilters)}
          >
            {showFilters ? 'Hide Metadata Filters' : 'Filter by Part Number / Revision'}
          </button>

          {error && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>
              Notice: {error}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
