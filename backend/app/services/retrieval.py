import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chunk
from app.services.embeddings import get_provider


async def retrieve(
    session: AsyncSession,
    query: str,
    owner_ids: list[uuid.UUID],
    k: int = 6,
) -> list[Chunk]:
    if not owner_ids:
        return []
    [qvec] = await get_provider().embed([query])
    stmt = (
        select(Chunk)
        .where(Chunk.owner_id.in_(owner_ids))
        .order_by(Chunk.embedding.cosine_distance(qvec))
        .limit(k)
    )
    return list((await session.execute(stmt)).scalars())
