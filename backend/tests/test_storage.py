"""
Tests for StorageService provider semantics:
1. local mode does not call Azure
2. azure mode requires configuration
3. azure mode propagates upload failure
4. auto mode falls back to local when Azure is not configured
5. successful Azure upload still records azure_blob_url metadata
6. auto mode propagates upload failure when Azure is configured
"""

from unittest.mock import MagicMock, patch
import pytest

from app.core.config import settings
from app.services.storage import (
    StorageService,
    StorageError,
    StorageConfigurationError,
    StorageUploadError,
)
from app.services.document_service import DocumentService
from app.services.document_processing.processor import DocumentProcessingError, ProcessedDocumentResult
from app.models.document import DocumentStatus


DUMMY_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=https;"
    "AccountName=stengcopilot06724;"
    "AccountKey=dummykey1234567890abcdef==;"
    "EndpointSuffix=core.windows.net"
)

DUMMY_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


def test_storage_local_mode_does_not_call_azure(monkeypatch):
    """STORAGE_PROVIDER='local' never attempts Azure Blob Storage even if connection string is set."""
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "local")
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONNECTION_STRING", DUMMY_CONNECTION_STRING)

    with patch("azure.storage.blob.BlobServiceClient.from_connection_string") as mock_bsc:
        url = StorageService.upload_document_blob("doc-1", "spec.pdf", b"pdfcontent")
        assert url is None
        mock_bsc.assert_not_called()

        data = StorageService.download_document_blob("doc-1", "spec.pdf")
        assert data is None
        mock_bsc.assert_not_called()


def test_storage_azure_mode_requires_configuration(monkeypatch):
    """STORAGE_PROVIDER='azure' raises StorageConfigurationError if connection string is missing or empty."""
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "azure")
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONNECTION_STRING", None)

    with pytest.raises(StorageConfigurationError) as exc_info:
        StorageService.upload_document_blob("doc-1", "spec.pdf", b"pdfcontent")
    assert "AZURE_STORAGE_CONNECTION_STRING" in str(exc_info.value)

    with pytest.raises(StorageConfigurationError) as exc_info_down:
        StorageService.download_document_blob("doc-1", "spec.pdf")
    assert "AZURE_STORAGE_CONNECTION_STRING" in str(exc_info_down.value)

    # Empty string should also fail
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONNECTION_STRING", "   ")
    with pytest.raises(StorageConfigurationError):
        StorageService.upload_document_blob("doc-1", "spec.pdf", b"pdfcontent")


def test_storage_azure_mode_propagates_upload_failure(monkeypatch):
    """STORAGE_PROVIDER='azure' propagates StorageUploadError when upload fails instead of returning None."""
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "azure")
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONNECTION_STRING", DUMMY_CONNECTION_STRING)

    with patch("azure.storage.blob.BlobServiceClient.from_connection_string") as mock_bsc:
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_blob = MagicMock()
        mock_blob.upload_blob.side_effect = Exception("Connection timeout to Azure endpoint")
        mock_container.get_blob_client.return_value = mock_blob
        mock_client.get_container_client.return_value = mock_container
        mock_bsc.return_value = mock_client

        with pytest.raises(StorageUploadError) as exc_info:
            StorageService.upload_document_blob("doc-1", "spec.pdf", b"pdfcontent")
        assert "Connection timeout" in str(exc_info.value)


def test_storage_auto_mode_falls_back_to_local_when_not_configured(monkeypatch):
    """STORAGE_PROVIDER='auto' falls back to local (returns None) without error when Azure is not configured."""
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "auto")
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONNECTION_STRING", None)

    with patch("azure.storage.blob.BlobServiceClient.from_connection_string") as mock_bsc:
        url = StorageService.upload_document_blob("doc-1", "spec.pdf", b"pdfcontent")
        assert url is None
        mock_bsc.assert_not_called()

        data = StorageService.download_document_blob("doc-1", "spec.pdf")
        assert data is None
        mock_bsc.assert_not_called()


def test_storage_auto_mode_propagates_failure_when_configured(monkeypatch):
    """STORAGE_PROVIDER='auto' does NOT silently ignore failures when Azure is configured."""
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "auto")
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONNECTION_STRING", DUMMY_CONNECTION_STRING)

    with patch("azure.storage.blob.BlobServiceClient.from_connection_string") as mock_bsc:
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_blob = MagicMock()
        mock_blob.upload_blob.side_effect = Exception("Azure 403 Forbidden")
        mock_container.get_blob_client.return_value = mock_blob
        mock_client.get_container_client.return_value = mock_container
        mock_bsc.return_value = mock_client

        with pytest.raises(StorageUploadError) as exc_info:
            StorageService.upload_document_blob("doc-1", "spec.pdf", b"pdfcontent")
        assert "Azure 403 Forbidden" in str(exc_info.value)


def test_storage_successful_azure_upload_returns_url(monkeypatch):
    """Successful Azure upload in 'azure' mode returns the blob URL under {doc_id}/{filename}."""
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "azure")
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONNECTION_STRING", DUMMY_CONNECTION_STRING)
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONTAINER_NAME", "documents")

    expected_url = "https://stengcopilot06724.blob.core.windows.net/documents/doc-123/spec.pdf"

    with patch("azure.storage.blob.BlobServiceClient.from_connection_string") as mock_bsc:
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_blob = MagicMock()
        mock_blob.url = expected_url
        mock_container.get_blob_client.return_value = mock_blob
        mock_client.get_container_client.return_value = mock_container
        mock_bsc.return_value = mock_client

        url = StorageService.upload_document_blob("doc-123", "spec.pdf", b"pdfcontent")
        assert url == expected_url
        mock_client.get_container_client.assert_called_once_with("documents")
        mock_container.get_blob_client.assert_called_once_with("doc-123/spec.pdf")
        mock_blob.upload_blob.assert_called_once_with(b"pdfcontent", overwrite=True)


@pytest.mark.asyncio
async def test_document_service_local_mode_does_not_set_azure_url(db_session, monkeypatch, tmp_path):
    """When STORAGE_PROVIDER='local', document ingestion succeeds without azure_blob_url."""
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "local")
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONNECTION_STRING", DUMMY_CONNECTION_STRING)
    monkeypatch.setattr(settings, "DOCUMENTS_STORAGE_DIR", str(tmp_path / "documents"))

    with patch("azure.storage.blob.BlobServiceClient.from_connection_string") as mock_bsc:
        with patch("app.services.document_service.process_pdf_document") as mock_proc:
            mock_proc.return_value = ProcessedDocumentResult(
                total_pages=1,
                processed_pages=1,
                ocr_pages=0,
                pages=[]
            )
            doc, result = await DocumentService.process_and_store_document(
                db=db_session,
                file_bytes=DUMMY_PDF_BYTES,
                original_filename="pump_spec.pdf",
                document_type="SPECIFICATION",
                part_number="PUMP-001",
                revision="A"
            )
            mock_bsc.assert_not_called()
            assert doc.status == DocumentStatus.PROCESSED
            assert doc.metadata_payload is not None
            assert "azure_blob_url" not in doc.metadata_payload


@pytest.mark.asyncio
async def test_document_service_records_azure_blob_url_on_success(db_session, monkeypatch, tmp_path):
    """When Azure upload succeeds, document ingestion records azure_blob_url in metadata_payload."""
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "azure")
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONNECTION_STRING", DUMMY_CONNECTION_STRING)
    monkeypatch.setattr(settings, "DOCUMENTS_STORAGE_DIR", str(tmp_path / "documents"))

    expected_url = "https://stengcopilot06724.blob.core.windows.net/documents/doc-id/pump_spec.pdf"

    with patch("app.services.storage.StorageService.upload_document_blob", return_value=expected_url) as mock_upload:
        with patch("app.services.document_service.process_pdf_document") as mock_proc:
            mock_proc.return_value = ProcessedDocumentResult(
                total_pages=1,
                processed_pages=1,
                ocr_pages=0,
                pages=[]
            )
            doc, result = await DocumentService.process_and_store_document(
                db=db_session,
                file_bytes=DUMMY_PDF_BYTES,
                original_filename="pump_spec.pdf",
                document_type="SPECIFICATION",
                part_number="PUMP-001",
                revision="A"
            )
            mock_upload.assert_called_once()
            assert doc.status == DocumentStatus.PROCESSED
            assert doc.metadata_payload is not None
            assert doc.metadata_payload.get("azure_blob_url") == expected_url


@pytest.mark.asyncio
async def test_document_service_propagates_azure_failure_in_azure_mode(db_session, monkeypatch, tmp_path):
    """When STORAGE_PROVIDER='azure' and upload fails, DocumentService sets status FAILED and raises error."""
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "azure")
    monkeypatch.setattr(settings, "AZURE_STORAGE_CONNECTION_STRING", DUMMY_CONNECTION_STRING)
    monkeypatch.setattr(settings, "DOCUMENTS_STORAGE_DIR", str(tmp_path / "documents"))

    with patch("app.services.storage.StorageService.upload_document_blob", side_effect=StorageUploadError("Blob storage failed: 500")):
        with pytest.raises(StorageUploadError) as exc_info:
            await DocumentService.process_and_store_document(
                db=db_session,
                file_bytes=DUMMY_PDF_BYTES,
                original_filename="pump_spec.pdf",
                document_type="SPECIFICATION",
                part_number="PUMP-001",
                revision="A"
            )
        assert "Blob storage failed" in str(exc_info.value)
