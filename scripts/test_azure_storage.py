import os
import sys
import uuid
import subprocess
from pathlib import Path

# Add backend to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.services.storage import StorageService

# Load from backend/.env.azure if available
env_azure_path = BACKEND_DIR / ".env.azure"
if env_azure_path.exists():
    with open(env_azure_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# 1. Obtain connection string securely without printing it
conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
if not conn_str:
    try:
        proc = subprocess.run(
            [
                "az.cmd" if sys.platform == "win32" else "az",
                "storage",
                "account",
                "show-connection-string",
                "--name",
                "stengcopilot06724",
                "--resource-group",
                "rg-engineering-copilot",
                "--query",
                "connectionString",
                "-o",
                "tsv",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        conn_str = proc.stdout.strip()
    except Exception as e:
        print(f"Error obtaining connection string from Azure CLI: {e}")
        sys.exit(1)

# Configure settings without exposing secret
settings.STORAGE_PROVIDER = "azure"
settings.AZURE_STORAGE_CONNECTION_STRING = conn_str
settings.AZURE_STORAGE_CONTAINER_NAME = "documents"

# 2. Setup unique test blob path
test_run_id = uuid.uuid4().hex[:12]
doc_id = f"m9-verification/{test_run_id}"
filename = "test.txt"
expected_blob_path = f"{doc_id}/{filename}"
test_payload = f"M9 Azure Blob Storage verification payload - run {test_run_id}\nTimestamp: 2026-10-06".encode("utf-8")

upload_status = "FAIL"
download_status = "FAIL"
content_match_status = "FAIL"
cleanup_status = "FAIL"

try:
    # 3. Upload small known payload using StorageService
    blob_url = StorageService.upload_document_blob(doc_id, filename, test_payload)
    if blob_url and "stengcopilot06724.blob.core.windows.net/documents/" in blob_url:
        upload_status = "PASS"

    # 4. Download the same blob using StorageService
    downloaded_data = StorageService.download_document_blob(doc_id, filename)
    if downloaded_data is not None:
        download_status = "PASS"

    # 5. Verify exact content match
    if downloaded_data == test_payload:
        content_match_status = "PASS"

except Exception as e:
    print(f"Error during verification: {e}")

finally:
    # 6. Cleanup ONLY this temporary test blob
    try:
        from azure.storage.blob import BlobServiceClient
        client = BlobServiceClient.from_connection_string(conn_str)
        container_client = client.get_container_client("documents")
        blob_client = container_client.get_blob_client(expected_blob_path)
        blob_client.delete_blob()
        cleanup_status = "PASS"
    except Exception as e:
        print(f"Error during cleanup: {e}")

print("--------------------------------------------------")
print(f"upload: {upload_status}")
print(f"download: {download_status}")
print(f"content match: {content_match_status}")
print(f"cleanup: {cleanup_status}")
print(f"exact test blob path: {expected_blob_path}")
all_passed = (
    upload_status == "PASS"
    and download_status == "PASS"
    and content_match_status == "PASS"
    and cleanup_status == "PASS"
)
print(f"live Azure Storage integration VERIFIED: {'YES' if all_passed else 'NO'}")
print("--------------------------------------------------")
sys.exit(0 if all_passed else 1)
