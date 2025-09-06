from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseModel  # -> your abstract base with UUID/timestamps

if TYPE_CHECKING:
    from .saved_search import SavedSearch


class Client(BaseModel):
    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))
    messenger_psid: Mapped[str | None] = mapped_column(String(64))

    sms_opt_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_opt_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    messenger_opt_in: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    __table_args__ = (CheckConstraint("name <> ''", name="ck_clients_name_not_empty"),)

    # One-to-many: Client -> SavedSearch
    searches: Mapped[list[SavedSearch]] = relationship(
        "SavedSearch",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
