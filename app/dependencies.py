from redis.asyncio import Redis
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,
)


def get_db():
    with Session(engine) as session:
        yield session


async def get_redis():
    # TODO: use context manager
    redis = Redis.from_url(settings.REDIS_URL)
    try:
        yield redis
    finally:
        await redis.close()
