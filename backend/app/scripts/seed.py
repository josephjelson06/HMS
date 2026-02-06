import asyncio

from app.core.database import AsyncSessionLocal
from app.core.seed import seed_initial_data


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)


if __name__ == "__main__":
    asyncio.run(main())
