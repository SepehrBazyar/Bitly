import base64

from redis.asyncio import Redis
from sqlmodel import Session, select

from .models import (
    URL,
    Visit,
)


async def create_short_url(db: Session, redis: Redis, long_url: str) -> str:
    counter = await redis.incr("url_counter")
    short_code = base64.urlsafe_b64encode(counter.to_bytes(8, "big")).decode().rstrip("=")

    url = URL(original_url=long_url, short_code=short_code)
    db.add(url)
    db.commit()
    db.refresh(url)

    await redis.set(f"url:{short_code}", long_url)
    return short_code


async def get_original_url(db: Session, redis: Redis, short_code: str) -> str:
    long_url = await redis.get(f"url:{short_code}")
    if long_url:
        return long_url.decode()

    stmt = select(URL).where(URL.short_code == short_code)
    url = db.exec(stmt).first()
    if not url:
        return None

    await redis.set(f"url:{short_code}", url.original_url)
    return url.original_url


async def log_visit(db: Session, redis: Redis, short_code: str, ip: str):
    stmt = select(URL).where(URL.short_code == short_code)
    url = db.exec(stmt).first()
    if url:
        visit = Visit(url_id=url.id, ip=ip)
        db.add(visit)
        db.commit()
        await redis.incr(f"stats:{short_code}")


async def get_stats(redis: Redis, short_code: str) -> int:
    count = await redis.get(f"stats:{short_code}")
    return int(count) if count else 0
