from datetime import datetime, timezone
from enum import Flag, auto
from typing import Annotated

import sqlalchemy
import sqlmodel
from databases import Database
from sqlmodel import col

from ..bc import Broadcaster
from .base import TableBase


class Order(TableBase, table=True):
    # NOTE: there are no Pydantic ways to set the generated table's name, as per https://github.com/fastapi/sqlmodel/issues/159
    __tablename__ = "orders"  # pyright: ignore[reportAssignmentType]

    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    order_id: int
    ordered_at: Annotated[
        datetime,
        sqlmodel.Field(
            sa_column_kwargs={"server_default": sqlmodel.text("CURRENT_TIMESTAMP")}
        ),
    ]
    canceled_at: datetime | None = sqlmodel.Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )
    completed_at: datetime | None = sqlmodel.Field(
        default=None, sa_column=sqlmodel.Column(sqlmodel.DateTime(timezone=True))
    )


class ModifiedFlag(Flag):
    ORIGINAL = auto()
    INCOMING = auto()
    SUPPLIED = auto()
    RESOLVED = auto()
    PUT_BACK = auto()


class Table:
    modified_flag_bc = Broadcaster(ModifiedFlag.ORIGINAL)

    def __init__(self, database: Database):
        self._db = database

    async def insert(self, order_id: int) -> None:
        query = sqlmodel.insert(Order)
        await self._db.execute(query, {"order_id": order_id})
        self.modified_flag_bc.send(ModifiedFlag.INCOMING)

    @staticmethod
    def _update(order_id: int) -> sqlalchemy.Update:
        clause = col(Order.order_id) == order_id
        return sqlmodel.update(Order).where(clause)

    async def cancel(self, order_id: int) -> None:
        values = {"canceled_at": datetime.now(timezone.utc), "completed_at": None}
        await self._db.execute(self._update(order_id), values)
        self.modified_flag_bc.send(ModifiedFlag.RESOLVED)

    async def _complete(self, order_id: int) -> None:
        """
        Use `supply_all_and_complete` when the `supplied_at` fields of
        `ordered_items` table should be updated as well.
        """
        values = {"canceled_at": None, "completed_at": datetime.now(timezone.utc)}
        await self._db.execute(self._update(order_id), values)

    async def reset(self, order_id: int) -> None:
        values = {"canceled_at": None, "completed_at": None}
        await self._db.execute(self._update(order_id), values)
        self.modified_flag_bc.send(ModifiedFlag.PUT_BACK)

    async def by_order_id(self, order_id: int) -> Order | None:
        query = sqlmodel.select(Order).where(Order.order_id == order_id)
        row = await self._db.fetch_one(query)
        return Order.model_validate(row) if row else None

    async def select_all(self) -> list[Order]:
        query = sqlmodel.select(Order)
        return [Order.model_validate(m) async for m in self._db.iterate(query)]
