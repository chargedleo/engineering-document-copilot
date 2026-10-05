import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

export const CadViewerPlaceholder: React.FC = () => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem' }}>
      <div>
        <Card
          title="CAD Geometry Viewport"
          subtitle="Interactive 3D assembly and 2D blueprint rendering canvas (WebGL/Three.js integration ready)."
        >
          <div
            style={{
              height: '480px',
              backgroundColor: '#090d16',
              border: '2px dashed var(--border-color)',
              borderRadius: '6px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '1rem',
              color: 'var(--text-secondary)',
            }}
          >
            <div style={{ fontSize: '3rem' }}>🧊</div>
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                3D CAD Viewport Ready
              </p>
              <p style={{ fontSize: '0.85rem' }}>
                Supported Formats: STEP (.step, .stp), IGES (.iges), DXF, STL
              </p>
            </div>
            <span style={{ fontSize: '0.8rem', padding: '0.3rem 0.8rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px' }}>
              WebGL Engine Standby
            </span>
          </div>
        </Card>
      </div>

      <div>
        <Card title="Extracted CAD Metadata" subtitle="Geometric parameters & properties">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-primary)', borderRadius: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Sample Part Assembly</span>
              <p style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--accent-primary)' }}>TS-402-C (Turbine Rotor)</p>
              <div style={{ marginTop: '0.5rem' }}>
                <Badge variant="info">Inconel 718</Badge>
              </div>
            </div>

            <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Calculated Mass:</span>
                <span style={{ fontWeight: 500 }}>14.85 kg</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Volume:</span>
                <span style={{ fontWeight: 500 }}>1810.97 cm³</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Dimensions (L x D):</span>
                <span style={{ fontWeight: 500 }}>420mm x 85mm</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Tolerance Class:</span>
                <span style={{ fontWeight: 500 }}>ISO 2768-m</span>
              </div>
            </div>

            <div style={{ marginTop: '1rem' }}>
              <h4 style={{ fontSize: '0.85rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Bill of Materials (BOM) Nodes</h4>
              <ul style={{ listStyle: 'none', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <li>🔹 01: Main Shaft Forging (Qty: 1)</li>
                <li>🔹 02: Spline Coupling Hub (Qty: 1)</li>
                <li>🔹 03: Fastener Ring M8 (Qty: 6)</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
