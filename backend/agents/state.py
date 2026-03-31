from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class PaperInfo(TypedDict):
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str]
    published: str

class AgentState(TypedDict):
    # 用户输入
    query: str
    session_id: str
    user_id: str

    # 对话历史
    messages: Annotated[list, add_messages]

    # 各阶段数据
    papers: list[PaperInfo]        
    analysis: str                 
    report: str                   

    # 流程控制
    current_step: str            
    error: str | None             