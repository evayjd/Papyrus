import sys
import os
import json
import asyncio
import xml.etree.ElementTree as ET

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from backend.core.config import settings

app = Server("arxiv-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_papers",
            description="搜索 arXiv 上的论文",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "max_results": {
                        "type": "integer",
                        "description": "最多返回多少篇",
                        "default": settings.ARXIV_MAX_RESULTS,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_paper_detail",
            description="获取某篇论文的详细信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "arxiv_id": {
                        "type": "string",
                        "description": "arXiv 论文 ID，例如 2301.00001",
                    },
                },
                "required": ["arxiv_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "search_papers":
        return await search_papers(arguments)
    elif name == "get_paper_detail":
        return await get_paper_detail(arguments)
    else:
        raise ValueError(f"未知工具: {name}")


async def search_papers(arguments: dict) -> list[TextContent]:
    query = arguments["query"]
    max_results = arguments.get("max_results", settings.ARXIV_MAX_RESULTS)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            settings.ARXIV_API_URL,
            params={
                "search_query": f"all:{query}",
                "max_results": max_results,
                "sortBy": "relevance",
            },
            timeout=settings.ARXIV_TIMEOUT,
        )

    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    papers = []
    for entry in root.findall("atom:entry", ns):
        arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]
        title = entry.find("atom:title", ns).text.strip()
        abstract = entry.find("atom:summary", ns).text.strip()
        published = entry.find("atom:published", ns).text[:10]
        authors = [
            a.find("atom:name", ns).text
            for a in entry.findall("atom:author", ns)
        ]

        papers.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": abstract[:500],
            "published": published,
            "authors": authors[:3],
        })

    return [TextContent(type="text", text=json.dumps(papers, ensure_ascii=False))]


async def get_paper_detail(arguments: dict) -> list[TextContent]:
    arxiv_id = arguments["arxiv_id"]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            settings.ARXIV_API_URL,
            params={"id_list": arxiv_id},
            timeout=settings.ARXIV_TIMEOUT,
        )

    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entry = root.find("atom:entry", ns)

    if entry is None:
        return [TextContent(type="text", text=json.dumps({"error": "论文不存在"}))]

    paper = {
        "arxiv_id": arxiv_id,
        "title": entry.find("atom:title", ns).text.strip(),
        "abstract": entry.find("atom:summary", ns).text.strip(),
        "published": entry.find("atom:published", ns).text[:10],
        "authors": [
            a.find("atom:name", ns).text
            for a in entry.findall("atom:author", ns)
        ],
    }

    return [TextContent(type="text", text=json.dumps(paper, ensure_ascii=False))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())