import React, { useRef } from 'react';
import { useDocuments } from '../../hooks/useDocuments';

export const DocumentList: React.FC = () => {
  const { documents, loading, error, uploadDocument, refresh } = useDocuments();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    let detectedType = 'SPECIFICATION';
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext === 'pdf' || ext === 'docx') detectedType = 'SPECIFICATION';
    else if (ext === 'step' || ext === 'stp' || ext === 'iges' || ext === 'stl') detectedType = 'DRAWING';
    else if (ext === 'dxf' || ext === 'dwg') detectedType = 'DRAWING';
    else if (ext === 'xlsx' || ext === 'csv') detectedType = 'BOM';

    await uploadDocument(file, detectedType as any);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'PROCESSED':
      case 'COMPLETED':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontWeight: 600 }}>
            <span>●</span>
            <span>PROCESSED</span>
          </span>
        );
      case 'PROCESSING':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', color: 'var(--text-secondary)' }}>
            <span>○</span>
            <span>PROCESSING</span>
          </span>
        );
      case 'FAILED':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontWeight: 700 }}>
            <span>✕</span>
            <span>FAILED</span>
          </span>
        );
      default:
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', color: 'var(--text-muted)' }}>
            <span>○</span>
            <span>PENDING</span>
          </span>
        );
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="registry-view">
      <div className="registry-header">
        <div>
          <h1 className="registry-title">Document Registry</h1>
          <p className="registry-subtitle">
            Verified engineering specifications, standard manuals, and CAD assemblies staged for indexing.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleFileUpload}
          />
          <button
            type="button"
            className="btn-primary"
            onClick={() => fileInputRef.current?.click()}
          >
            Upload Specification
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => refresh()}
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="abstention-notice">
          <span className="abstention-heading">Registry Notice</span>
          <p className="abstention-body">{error}</p>
        </div>
      )}

      {loading && (
        <div className="loading-indicator pulse-monochrome">
          <span>●</span>
          <span>Loading verified document records...</span>
        </div>
      )}

      {!loading && documents.length === 0 && (
        <div style={{ border: '1px solid var(--border-subtle)', padding: '3.5rem 2rem', textAlign: 'center' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem', textTransform: 'uppercase' }}>
            No Documents Staged
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '480px', margin: '0 auto' }}>
            Upload engineering PDF manuals or CAD specifications to initiate structural chunking, OCR fallback, and hybrid vector indexing.
          </p>
        </div>
      )}

      {!loading && documents.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table className="registry-table">
            <thead>
              <tr>
                <th>Document / Filename</th>
                <th>Type</th>
                <th>Part Number</th>
                <th>Revision</th>
                <th>Pages</th>
                <th>Size</th>
                <th>Status</th>
                <th>Registered</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {doc.filename}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                    {doc.document_type || 'SPECIFICATION'}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                    {doc.part_number || '—'}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>
                    {doc.revision || '—'}
                  </td>
                  <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                    {doc.metadata_payload?.page_count
                      ? `${doc.metadata_payload.page_count} ${
                          doc.metadata_payload.ocr_page_count
                            ? `(${doc.metadata_payload.ocr_page_count} OCR)`
                            : ''
                        }`
                      : '—'}
                  </td>
                  <td style={{ fontVariantNumeric: 'tabular-nums', color: 'var(--text-secondary)' }}>
                    {formatFileSize(doc.file_size_bytes)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
                    {getStatusLabel(doc.status)}
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {new Date(doc.created_at || doc.uploaded_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
