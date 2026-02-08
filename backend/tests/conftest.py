import os

# Ensure unit tests can run without requiring a local .env.
# If a caller sets real env vars (e.g., for integration tests), we don't override them.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost/test",
)
os.environ.setdefault(
    "JWT_SECRET",
    # >=32 chars to satisfy startup guards when lifespans are enabled.
    "this-is-a-very-strong-test-secret-1234567890",
)
os.environ.setdefault("SEED_DATA", "false")

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
