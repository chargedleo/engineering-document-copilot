import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Test 1: Health endpoint returns status healthy."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_readiness_check(async_client: AsyncClient):
    """Test 2: Readiness check verifies database is connected."""
    response = await async_client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "azure_openai_configured" in data
    assert "azure_search_configured" in data


@pytest.mark.asyncio
async def test_database_connectivity_direct(db_session: AsyncSession):
    """Test 3: Direct database session connectivity query."""
    result = await db_session.execute(text("SELECT 1 AS alive"))
    row = result.scalar_one()
    assert row == 1


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Test root landing information endpoint."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "health" in data
