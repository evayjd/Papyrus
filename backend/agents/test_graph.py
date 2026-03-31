import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from backend.agents.graph import papyrus_graph

async def test():
    result = await papyrus_graph.ainvoke({
        "query": "RAG retrieval augmented generation",
        "session_id": "test-session",
        "user_id": "test-user",
        "messages": [],
        "papers": [],
        "analysis": "",
        "report": "",
        "current_step": "",
        "error": None,
    })

    print("=== 检索到的论文 ===")
    for p in result["papers"]:
        print(f"- {p['title']}")

    print("\n=== 分析结果 ===")
    print(result["analysis"][:500])

    print("\n=== 报告片段 ===")
    print(result["report"][:500])

asyncio.run(test())