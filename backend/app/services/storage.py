import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("engineering_copilot.storage")


class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class StorageConfigurationError(StorageError):
    """Raised when required storage configuration is missing or invalid."""
    pass


class StorageUploadError(StorageError):
    """Raised when an upload to storage fails."""
    pass


class StorageService:
    """Service for handling document file persistence across Local and Azure Blob Storage."""

    @staticmethod
    def get_storage_provider() -> str:
        provider = getattr(settings, "STORAGE_PROVIDER", "local")
        return (provider or "local").lower().strip()

    @staticmethod
    def is_azure_configured() -> bool:
        conn = getattr(settings, "AZURE_STORAGE_CONNECTION_STRING", None)
        return bool(conn and str(conn).strip())

    @staticmethod
    def should_use_azure() -> bool:
        provider = StorageService.get_storage_provider()
        if provider == "local":
            return False
        if provider == "azure":
            return True
        if provider == "auto":
            return StorageService.is_azure_configured()
        raise StorageConfigurationError(
            f"Unsupported STORAGE_PROVIDER: '{provider}'. Supported values: 'local', 'azure', 'auto'."
        )

    @staticmethod
    def upload_document_blob(doc_id: str, filename: str, data: bytes) -> Optional[str]:
        """
        Uploads document bytes to Azure Blob Storage under {doc_id}/{filename}.
        Returns blob URL if successful.

        Semantics:
        - STORAGE_PROVIDER='local': Never attempts Azure Blob Storage; returns None.
        - STORAGE_PROVIDER='azure': Requires Azure configuration (raises StorageConfigurationError if missing).
          Uploads to Azure and raises StorageUploadError on failure (does not return None).
        - STORAGE_PROVIDER='auto': Uses Azure if configured (raising StorageUploadError on failure);
          falls back to local (returns None) if Azure is not configured.
        """
        provider = StorageService.get_storage_provider()

        if provider == "local":
            return None

        if provider == "azure":
            if not StorageService.is_azure_configured():
                raise StorageConfigurationError(
                    "Azure storage configuration is required when STORAGE_PROVIDER='azure'. "
                    "Missing AZURE_STORAGE_CONNECTION_STRING."
                )
        elif provider == "auto":
            if not StorageService.is_azure_configured():
                return None
        else:
            raise StorageConfigurationError(
                f"Unsupported STORAGE_PROVIDER: '{provider}'. Supported values: 'local', 'azure', 'auto'."
            )

        blob_name = f"{doc_id}/{filename}"
        container_name = getattr(settings, "AZURE_STORAGE_CONTAINER_NAME", None) or "documents"

        try:
            from azure.storage.blob import BlobServiceClient

            client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
            container_client = client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data, overwrite=True)
            logger.info(f"Successfully uploaded blob to Azure Storage: {container_name}/{blob_name}")
            return blob_client.url
        except Exception as e:
            logger.error(f"Failed to upload blob '{blob_name}' to Azure Storage: {e}", exc_info=True)
            raise StorageUploadError(f"Failed to upload blob '{blob_name}' to Azure Storage: {e}") from e

    @staticmethod
    def download_document_blob(doc_id: str, filename: str) -> Optional[bytes]:
        """
        Downloads document bytes from Azure Blob Storage if configured and available.
        """
        provider = StorageService.get_storage_provider()

        if provider == "local":
            return None

        if provider == "azure":
            if not StorageService.is_azure_configured():
                raise StorageConfigurationError(
                    "Azure storage configuration is required when STORAGE_PROVIDER='azure'. "
                    "Missing AZURE_STORAGE_CONNECTION_STRING."
                )
        elif provider == "auto":
            if not StorageService.is_azure_configured():
                return None
        else:
            raise StorageConfigurationError(
                f"Unsupported STORAGE_PROVIDER: '{provider}'. Supported values: 'local', 'azure', 'auto'."
            )

        blob_name = f"{doc_id}/{filename}"
        container_name = getattr(settings, "AZURE_STORAGE_CONTAINER_NAME", None) or "documents"

        try:
            from azure.storage.blob import BlobServiceClient

            client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
            blob_client = client.get_blob_client(container=container_name, blob=blob_name)
            stream = blob_client.download_blob()
            return stream.readall()
        except Exception as e:
            logger.error(f"Failed to download blob '{blob_name}' from Azure Storage: {e}")
            if provider == "azure":
                raise StorageError(f"Failed to download blob '{blob_name}': {e}") from e
            return None
