from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
)
from redis.asyncio import Redis
from sqlmodel import Session

from app.crud import (
    create_short_url,
    get_original_url,
    get_stats,
    log_visit,
)
from app.dependencies import get_db, get_redis
from app.schemas import (
    ShortenRequest,
    ShortenResponse,
    StatsResponse,
)

router = APIRouter()


@router.post("/shorten", response_model=ShortenResponse)
async def shorten_url(
    request: ShortenRequest,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    short_code = await create_short_url(db, redis, str(request.long_url))
    return ShortenResponse(short_code=short_code)


@router.get("/{short_code}")
async def redirect(
    request: Request,
    short_code: str,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    long_url = await get_original_url(db, redis, short_code)
    if not long_url:
        raise HTTPException(404, "Not found")

    await log_visit(db, redis, short_code, request.client.host)
    return Response(status_code=302, headers={"Location": long_url})


@router.get("/stats/{short_code}", response_model=StatsResponse)
async def stats(
    short_code: str,
    redis: Redis = Depends(get_redis),
):
    count = await get_stats(redis, short_code)
    return StatsResponse(visit_count=count)
