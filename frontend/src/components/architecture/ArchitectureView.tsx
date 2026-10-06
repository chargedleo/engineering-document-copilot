import React from 'react';

export const ArchitectureView: React.FC = () => {
  return (
    <div className="arch-view">
      <div className="registry-header" style={{ marginBottom: '1rem' }}>
        <div>
          <h1 className="registry-title">System Architecture</h1>
          <p className="registry-subtitle">
            Engineering document intelligence and CAD knowledge copilot platform topology.
          </p>
        </div>
        <div>
          <span className="brand-badge">Milestone 10 · System Architecture</span>
        </div>
      </div>

      <div className="arch-section">
        <h2 className="arch-header">01 · Autonomous Agent & Graph Workflow</h2>
        <p className="arch-text">
          Built on a compiled LangGraph <code>StateGraph</code> with typed state transitions:
          <code>classify_and_plan</code> → <code>execute_tools</code> → <code>synthesize_answer</code>.
          The agent dynamically plans tool execution based on user queries, supporting multi-tool composite workflows
          such as retrieving engineering pressures and chaining values into unit conversions.
        </p>
      </div>

      <div className="arch-section">
        <h2 className="arch-header">02 · Engineering Tool Suite & Constraints</h2>
        <p className="arch-text">
          Tools are isolated and deterministic with zero arbitrary code execution:
        </p>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
          <div><code>search_engineering_documents</code> — Hybrid BM25 keyword + dense vector search with Reciprocal Rank Fusion (RRF).</div>
          <div><code>get_document_metadata</code> — PostgreSQL relational lookup for verified document revisions, status, and page counts.</div>
          <div><code>calculate_engineering</code> — Constrained unit conversions (bar/psi, °C/°F, m³/h / LPM, kW/HP) and percentage deltas.</div>
        </div>
      </div>

      <div className="arch-section">
        <h2 className="arch-header">03 · Document Intelligence & OCR Pipeline</h2>
        <p className="arch-text">
          Ingestion parses technical PDFs page by page with PyMuPDF. Pages with insufficient selectable text
          automatically trigger high-resolution rendering (300 DPI), OpenCV preprocessing (grayscale, Gaussian noise reduction,
          Otsu binarization), and Tesseract OCR title block extraction.
        </p>
      </div>

      <div className="arch-section">
        <h2 className="arch-header">04 · Grounded Citations & Security Boundary</h2>
        <p className="arch-text">
          Retrieved chunks are passed inside untrusted <code>&lt;engineering_context&gt;</code> XML tags, isolating
          retrieved text from instruction prompts. The agent enforces strict engineering fidelity with in-text citation tags
          (<code>[C1]</code>, <code>[C2]</code>) linked directly to document filenames, page numbers, and chunk indexes.
          When evidence is insufficient, the system returns standardized engineering abstention.
        </p>
      </div>

      <div className="arch-section">
        <h2 className="arch-header">05 · Dual-Provider Deployment Abstraction</h2>
        <p className="arch-text">
          Abstract provider interfaces decouple local deterministic execution from cloud dependencies.
          The system runs hermetically with <code>LocalMockChatProvider</code> and <code>LocalMockEmbeddingProvider</code>,
          and is verified live against Azure OpenAI (<code>gpt-4o</code> + <code>text-embedding-3-small</code>),
          Azure AI Search (<code>engineering-docs-index</code>), Azure PostgreSQL Flexible Server, and Azure Blob Storage.
          Backend container cloud compute hosting remains a future deployment step.
        </p>
      </div>
    </div>
  );
};
