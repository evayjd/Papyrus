from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from backend.agents.state import AgentState, PaperInfo
from backend.core.config import settings
import httpx
import xml.etree.ElementTree as ET
import json

llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
)

# --- Supervisor ---

async def supervisor_node(state: AgentState) -> dict:
    query = state["query"]
    return {
        "current_step": "search",
        "messages": [AIMessage(content=f"收到研究请求：{query}，开始检索相关论文。")],
    }


# --- Search ---

async def search_node(state: AgentState) -> dict:
    query = state["query"]

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(
            settings.ARXIV_API_URL,
            params={
                "search_query": f"all:{query}",
                "max_results": settings.ARXIV_MAX_RESULTS,
                "sortBy": "relevance",
            },
            timeout=settings.ARXIV_TIMEOUT,
        )

    if not response.text or response.status_code != 200:
        return {
            "papers": [],
            "current_step": "dedupe",
            "messages": [AIMessage(content=f"检索失败，状态码：{response.status_code}")],
            "error": f"arXiv API 返回异常：{response.status_code}",
        }
    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    papers: list[PaperInfo] = []
    for entry in root.findall("atom:entry", ns):
        id_elem = entry.find("atom:id", ns)
        title_elem = entry.find("atom:title", ns)
        abstract_elem = entry.find("atom:summary", ns)
        published_elem = entry.find("atom:published", ns)
        author_elems = entry.findall("atom:author", ns)

        if id_elem is None or title_elem is None:
            continue

        arxiv_id = id_elem.text.split("/abs/")[-1] if id_elem.text else ""
        authors = []
        for a in author_elems[:3]:
            name_elem = a.find("atom:name", ns)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text)

        papers.append(PaperInfo(
            arxiv_id=arxiv_id,
            title=title_elem.text.strip() if title_elem.text else "",
            abstract=abstract_elem.text.strip()[:500] if abstract_elem is not None and abstract_elem.text else "",
            authors=authors,
            published=published_elem.text[:10] if published_elem is not None and published_elem.text else "",
        ))

    return {
        "papers": papers,
        "current_step": "dedupe",
        "messages": [AIMessage(content=f"检索到 {len(papers)} 篇相关论文。")],
    }


# --- Dedupe ---

async def dedupe_node(state: AgentState) -> dict:
    papers = state["papers"]
    seen = set()
    unique_papers = []
    for paper in papers:
        if paper["arxiv_id"] not in seen:
            seen.add(paper["arxiv_id"])
            unique_papers.append(paper)

    return {
        "papers": unique_papers,
        "current_step": "analyze",
        "messages": [AIMessage(content=f"去重后保留 {len(unique_papers)} 篇论文。")],
    }


# --- Analyze ---

async def analyze_node(state: AgentState) -> dict:
    query = state["query"]
    papers = state["papers"]

    papers_text = "\n\n".join([
        f"标题: {p['title']}\n摘要: {p['abstract']}"
        for p in papers
    ])

    prompt = f"""你是一个学术研究助手。用户想研究以下课题：
{query}

以下是检索到的相关论文：
{papers_text}

请对这些论文进行分析，包括：
1. 主要研究方向和方法
2. 各论文之间的异同点
3. 该领域的研究趋势
4. 值得深入阅读的论文推荐

请用中文回答。"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {
        "analysis": response.content,
        "current_step": "writer",
        "messages": [AIMessage(content="分析完成，正在生成报告。")],
    }


# --- Writer ---

async def writer_node(state: AgentState) -> dict:
    query = state["query"]
    papers = state["papers"]
    analysis = state["analysis"]

    papers_list = "\n".join([
        f"- {p['title']} ({p['published']}) - {', '.join(p['authors'])}"
        for p in papers
    ])

    prompt = f"""基于以下信息，生成一份结构化的研究报告：

研究课题：{query}

检索到的论文：
{papers_list}

分析结果：
{analysis}

请生成一份包含以下部分的 Markdown 格式报告：
1. 研究概述
2. 主要发现
3. 论文列表
4. 研究趋势
5. 结论与建议

请用中文撰写。"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {
        "report": response.content,
        "current_step": "done",
        "messages": [AIMessage(content="报告生成完成！")],
    }