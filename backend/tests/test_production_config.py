"""
Tests for Milestone 8 production configuration, environment handling,
health checks, and container deployment specifications.
"""
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.config import Settings


@pytest.mark.asyncio
async def test_health_liveness_endpoint(async_client: AsyncClient):
    """Verify standard liveness health check returns 200 with system metadata."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "environment" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_readiness_connected(async_client: AsyncClient):
    """Verify readiness check passes when database connection is healthy."""
    response = await async_client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_readiness_degraded_on_db_error(async_client: AsyncClient):
    """Verify readiness check responds with 503 Service Unavailable when DB fails."""
    with patch("app.api.v1.endpoints.health.get_db") as mock_get_db:
        # Mock session that raises database connection error
        mock_session = AsyncMock()
        mock_session.execute.side_effect = ConnectionRefusedError("Database unreachable")
        
        async def override_get_db():
            yield mock_session

        from app.main import app
        from app.core.database import get_db
        app.dependency_overrides[get_db] = override_get_db

        try:
            response = await async_client.get("/api/v1/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "degraded"
            assert "unreachable" in data["database"]
        finally:
            app.dependency_overrides.pop(get_db, None)


def test_settings_cors_origins_parsing():
    """Verify CORS origins string comma separation and list parsing."""
    settings_str = Settings(CORS_ORIGINS="http://localhost:3000, http://localhost:5173")
    assert "http://localhost:3000" in settings_str.CORS_ORIGINS
    assert "http://localhost:5173" in settings_str.CORS_ORIGINS

    settings_list = Settings(CORS_ORIGINS=["http://localhost:8000"])
    assert settings_list.CORS_ORIGINS == ["http://localhost:8000"]


def test_settings_storage_paths_default():
    """Verify storage paths default to data directories in repository."""
    settings = Settings()
    assert Path(settings.DOCUMENTS_STORAGE_DIR).name == "documents"
    assert Path(settings.PROCESSED_STORAGE_DIR).name == "processed"


def test_dockerfile_production_specifications():
    """Verify backend Dockerfile exists and enforces non-root security and healthchecks."""
    backend_dir = Path(__file__).resolve().parent.parent
    dockerfile_path = backend_dir / "Dockerfile"
    assert dockerfile_path.exists(), "backend/Dockerfile must exist"

    content = dockerfile_path.read_text(encoding="utf-8")
    assert "USER appuser" in content, "Dockerfile must run as non-root user"
    assert "HEALTHCHECK" in content, "Dockerfile must define container healthcheck"
    assert "ENTRYPOINT" in content, "Dockerfile must define entrypoint"
    assert "tesseract-ocr" in content, "Dockerfile must install Linux Tesseract OCR"
    assert "libgl1" in content, "Dockerfile must include OpenGL library for OpenCV"


def test_backend_entrypoint_lf_line_endings():
    """Verify backend entrypoint script exists and maintains POSIX LF line endings."""
    backend_dir = Path(__file__).resolve().parent.parent
    entrypoint_path = backend_dir / "entrypoint.sh"
    assert entrypoint_path.exists(), "backend/entrypoint.sh must exist"

    raw_bytes = entrypoint_path.read_bytes()
    assert b"\r\n" not in raw_bytes, "backend/entrypoint.sh must have LF line endings for Linux execution"
    assert b"alembic upgrade head" in raw_bytes, "entrypoint.sh must manage schema migrations"


def test_docker_compose_root_structure():
    """Verify root docker-compose.yml defines postgres, backend, and frontend services."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    compose_path = root_dir / "docker-compose.yml"
    assert compose_path.exists(), "Root docker-compose.yml must exist"

    content = compose_path.read_text(encoding="utf-8")
    assert "postgres:" in content
    assert "backend:" in content
    assert "frontend:" in content
    assert "postgres_data:" in content
    assert "condition: service_healthy" in content
