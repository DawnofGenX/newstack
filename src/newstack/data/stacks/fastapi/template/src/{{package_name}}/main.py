"""HTTP API for {{ title }}."""

from __future__ import annotations

from itertools import count

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(ge=0)


class Item(ItemIn):
    id: int


def create_app() -> FastAPI:
    """Build the application. A factory keeps tests isolated from each other."""
    app = FastAPI(title="{{ title }}", version="0.1.0")
    items: dict[int, Item] = {}
    ids = count(1)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/items")
    def list_items() -> list[Item]:
        return list(items.values())

    @app.post("/items", status_code=201)
    def create_item(payload: ItemIn) -> Item:
        item = Item(id=next(ids), **payload.model_dump())
        items[item.id] = item
        return item

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> Item:
        try:
            return items[item_id]
        except KeyError:
            raise HTTPException(status_code=404, detail="item not found") from None

    return app


app = create_app()
