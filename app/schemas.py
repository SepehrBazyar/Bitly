from datetime import datetime

from pydantic import (
    BaseModel,
    HttpUrl,
)


class ShortenRequest(BaseModel):
    long_url: HttpUrl
    expire_at: datetime | None = None


class ShortenResponse(BaseModel):
    short_code: str


class StatsResponse(BaseModel):
    visit_count: int
