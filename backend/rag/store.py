from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from backend.db.models import Paper
from backend.rag.embeddings import embed_text, embed_texts
from rank_bm25 import BM25Okapi
import json
import uuid
from datetime import datetime, timezone

#存论文到数据库，如果存在则更新embedding和fetched_at字段，否则创建新记录
async def upsert_paper(db: AsyncSession, paper_data: dict) -> Paper:
    result = await db.execute(
        select(Paper).where(Paper.arxiv_id == paper_data["arxiv_id"])
    )
    paper = result.scalar_one_or_none()

    # 统一类型转换
    published_date = None
    raw_date = paper_data.get("published")
    if raw_date:
        if isinstance(raw_date, datetime):
            published_date = raw_date
        elif isinstance(raw_date, str):
            try:
                published_date = datetime.strptime(raw_date[:10], "%Y-%m-%d")
            except ValueError:
                published_date = None

    authors = paper_data.get("authors", [])
    if isinstance(authors, str):
        authors = [authors]

    title = str(paper_data.get("title", "")).strip() or None
    abstract = str(paper_data.get("abstract", "")).strip() or None

    text_to_embed = f"{title or ''} {abstract or ''}".strip()
    embedding = embed_text(text_to_embed) if text_to_embed else None

    if paper:
        paper.embedding = embedding
        paper.fetched_at = datetime.now(timezone.utc)
    else:
        paper = Paper(
            id=uuid.uuid4(),
            arxiv_id=paper_data["arxiv_id"],
            title=title,
            authors=authors,
            abstract=abstract,
            published_date=published_date,
            embedding=embedding,
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(paper)

    await db.flush()
    return paper

#找最相关论文
async def vector_search(db: AsyncSession, query: str, top_k: int = 10) -> list[Paper]:
    query_embedding = embed_text(query)
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    result = await db.execute(
        text("""
            SELECT id FROM papers
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """),
        {"embedding": embedding_str, "top_k": top_k},
    )
    ids = [row[0] for row in result.fetchall()]

    if not ids:
        return []

    result = await db.execute(select(Paper).where(Paper.id.in_(ids)))
    return list(result.scalars().all())

#基础bm25索引
async def bm25_search(db: AsyncSession, query: str, top_k: int = 10) -> list[Paper]:
    result = await db.execute(select(Paper))
    all_papers = result.scalars().all()

    if not all_papers:
        return []

    corpus = [f"{p.title} {p.abstract}" for p in all_papers]
    tokenized_corpus = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [all_papers[i] for i in top_indices]

#rrf
def reciprocal_rank_fusion(
    vector_results: list[Paper],
    bm25_results: list[Paper],
    k: int = 60,
) -> list[Paper]:
    scores: dict[str, float] = {}
    paper_map: dict[str, Paper] = {}

    for rank, paper in enumerate(vector_results):
        pid = str(paper.id)
        scores[pid] = scores.get(pid, 0) + 1 / (k + rank + 1)
        paper_map[pid] = paper

    for rank, paper in enumerate(bm25_results):
        pid = str(paper.id)
        scores[pid] = scores.get(pid, 0) + 1 / (k + rank + 1)
        paper_map[pid] = paper

    sorted_ids = sorted(scores, key=lambda pid: scores[pid], reverse=True)
    return [paper_map[pid] for pid in sorted_ids]

#对外暴露接口，先做向量搜索，如果结果不足，再做bm25搜索，最后融合排序
async def hybrid_search(db: AsyncSession, query: str, top_k: int = 5) -> list[Paper]:
    vector_results = await vector_search(db, query, top_k=10)
    bm25_results = await bm25_search(db, query, top_k=10)
    fused = reciprocal_rank_fusion(vector_results, bm25_results)
    return fused[:top_k]