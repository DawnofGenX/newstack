from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from .models import Base, Item

SEED = [("widget", 9.5), ("gadget", 19.0), ("gizmo", 4.25)]


async def make_engine(url: str = "sqlite+aiosqlite:///:memory:") -> AsyncEngine:
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


async def seed(engine: AsyncEngine) -> int:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        existing = await session.scalar(select(Item.id).limit(1))
        if existing is not None:
            return 0
        session.add_all([Item(name=name, price=price) for name, price in SEED])
        await session.commit()
        return len(SEED)


async def list_items(engine: AsyncEngine) -> list[Item]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        result = await session.execute(select(Item).order_by(Item.id))
        return list(result.scalars().all())


async def get_item(engine: AsyncEngine, item_id: int) -> Item | None:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        return await session.get(Item, item_id)