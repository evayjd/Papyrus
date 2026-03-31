import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from backend.db.database import AsyncSessionLocal
from backend.rag.store import upsert_paper, hybrid_search

async def test():
    async with AsyncSessionLocal() as db:
        # 存一篇假论文
        paper = await upsert_paper(db, {
            "arxiv_id": "2301.00001",
            "title": "Retrieval Augmented Generation for Large Language Models",
            "abstract": "We propose RAG, a method that combines retrieval with generation for knowledge-intensive NLP tasks.",
            "authors": ["Author One", "Author Two"],
            "published": "2023-01-01",
        })
        await db.commit()
        print(f"存入论文: {paper.title}")

        # 搜索
        results = await hybrid_search(db, "RAG retrieval generation", top_k=3)
        print(f"搜索结果: {len(results)} 篇")
        for r in results:
            print(f"  - {r.title}")

asyncio.run(test())