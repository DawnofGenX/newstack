import pytest

from {{ package_name }}.db import get_item, list_items, make_engine, seed


@pytest.mark.asyncio
async def test_seed_and_list():
    engine = await make_engine()
    n = await seed(engine)
    assert n == 3
    items = await list_items(engine)
    assert len(items) == 3
    item = await get_item(engine, 1)
    assert item is not None
    await engine.dispose()
