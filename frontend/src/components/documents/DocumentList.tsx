import React, { useRef } from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <Badge variant="success">Completed</Badge>;
      case 'PROCESSING':
        return <Badge variant="warning">Processing</Badge>;
      case 'FAILED':
        return <Badge variant="danger">Failed</Badge>;
      default:
        return <Badge variant="info">Pending</Badge>;
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div>
      <Card
        title="Engineering Documents & Specifications"
        subtitle="Manage technical specifications, datasheets, standard manuals, and CAD files staged for indexing."
        action={
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={handleFileUpload}
            />
            <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()}>
              <span>⬆️</span> Upload File
            </button>
            <button className="btn btn-secondary" onClick={() => refresh()}>
              Refresh
            </button>
          </div>
        }
      >
        {error && (
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '4px', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {loading && <p style={{ color: 'var(--text-secondary)' }}>Loading documents...</p>}

        {!loading && documents.length === 0 && (
          <div style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-secondary)' }}>
            <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>No engineering documents staged yet.</p>
            <p style={{ fontSize: '0.9rem' }}>Upload PDF specifications or CAD models (.step, .dxf) to initiate document processing.</p>
          </div>
        )}

        {!loading && documents.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Type</th>
                <th>Part Number</th>
                <th>Revision</th>
                <th>Size</th>
                <th>Status</th>
                <th>Date Added</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td style={{ fontWeight: 500 }}>{doc.filename}</td>
                  <td><Badge variant="info">{doc.document_type || 'SPECIFICATION'}</Badge></td>
                  <td>{doc.part_number || '-'}</td>
                  <td>{doc.revision || '-'}</td>
                  <td>{formatFileSize(doc.file_size_bytes)}</td>
                  <td>{getStatusBadge(doc.status)}</td>
                  <td style={{ color: 'var(--text-muted)' }}>
                    {new Date(doc.created_at || doc.uploaded_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
};
