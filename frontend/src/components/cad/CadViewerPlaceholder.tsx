import React from 'react';

export const CadViewerPlaceholder: React.FC = () => {
  return (
    <div className="cad-view">
      <div className="registry-header">
        <div>
          <h1 className="registry-title">CAD Attributes & Assemblies</h1>
          <p className="registry-subtitle">
            Geometric parameters, tolerance classes, and bill-of-materials structures cross-referenced with documentation.
          </p>
        </div>

        <div>
          <span className="brand-badge">STEP / IGES / DXF Ready</span>
        </div>
      </div>

      <div className="cad-viewport-grid">
        <div>
          <div className="technical-canvas">
            <div className="canvas-crosshair" />
            <div style={{ textAlign: 'center', zIndex: 1, backgroundColor: 'var(--canvas-bg)', padding: '1rem 1.5rem', border: '1px solid var(--border-medium)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                CAD Viewport Engine
              </div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.02em', marginTop: '0.25rem' }}>
                Geometric Canvas Standby
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.35rem', fontFamily: 'var(--font-mono)' }}>
                Formats: STEP (.step, .stp) · IGES (.iges) · DXF · STL
              </div>
            </div>
            <div style={{ position: 'absolute', bottom: '1rem', right: '1.25rem', fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              GRID: 24mm · AXIS: XYZ
            </div>
          </div>
        </div>

        <aside className="cad-sidebar">
          <div>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
              Sample Assembly Registry
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', marginTop: '0.25rem' }}>
              TS-402-C
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Turbine Rotor Assembly · Inconel 718
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div className="cad-metric-row">
              <span className="cad-metric-label">Calculated Mass</span>
              <span className="cad-metric-val">14.85 kg</span>
            </div>
            <div className="cad-metric-row">
              <span className="cad-metric-label">Volume</span>
              <span className="cad-metric-val">1810.97 cm³</span>
            </div>
            <div className="cad-metric-row">
              <span className="cad-metric-label">Dimensions (L × D)</span>
              <span className="cad-metric-val">420mm × 85mm</span>
            </div>
            <div className="cad-metric-row">
              <span className="cad-metric-label">Tolerance Class</span>
              <span className="cad-metric-val">ISO 2768-m</span>
            </div>
            <div className="cad-metric-row">
              <span className="cad-metric-label">Surface Finish</span>
              <span className="cad-metric-val">Ra 0.8 µm</span>
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
              Bill of Materials (BOM)
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>01 Main Shaft Forging</span>
                <span style={{ color: 'var(--text-muted)' }}>Qty: 1</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>02 Spline Coupling Hub</span>
                <span style={{ color: 'var(--text-muted)' }}>Qty: 1</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>03 Fastener Ring M8</span>
                <span style={{ color: 'var(--text-muted)' }}>Qty: 6</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>04 Bearing Journal Sleeve</span>
                <span style={{ color: 'var(--text-muted)' }}>Qty: 2</span>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};
