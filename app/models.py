from datetime import UTC, datetime

from sqlmodel import (
    Field,
    Relationship,
    SQLModel,
)


class URL(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    original_url: str
    short_code: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
    expire_at: datetime | None = Field(
        default=None,
        nullable=True,
    )
    visits: list["Visit"] = Relationship(back_populates="url")


class Visit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url_id: int = Field(foreign_key="url.id")
    ip: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
    url: URL | None = Relationship(back_populates="visits")
