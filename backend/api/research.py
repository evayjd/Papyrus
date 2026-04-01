from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import uuid
from datetime import datetime, timezone
import asyncio

from backend.db.database import get_db
from backend.db.models import Session, SessionStatus, Message, MessageRole, Report
from backend.agents.graph import papyrus_graph
from backend.api.deps import get_current_user
from backend.db.models import User
from backend.core.security import decode_access_token
from backend.core.observability import get_langfuse_callback
from backend.evaluation.ragas_eval import evaluate_report

router = APIRouter(prefix="/research", tags=["research"])


async def get_user_from_token(token: str, db: AsyncSession):
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


@router.websocket("/ws/{session_id}")
async def research_websocket(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    await websocket.accept()

    try:
        # 第一条消息必须是 token
        auth_data = await websocket.receive_json()
        token = auth_data.get("token")
        if not token:
            await websocket.send_json({"type": "error", "message": "未提供token"})
            await websocket.close()
            return

        user = await get_user_from_token(token, db)
        if not user:
            await websocket.send_json({"type": "error", "message": "token无效"})
            await websocket.close()
            return

        # 验证 session 归属
        result = await db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.user_id == user.id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            await websocket.send_json({"type": "error", "message": "session不存在"})
            await websocket.close()
            return

        # 接收用户的研究问题
        query_data = await websocket.receive_json()
        query = query_data.get("query", "")

        if not query:
            await websocket.send_json({"type": "error", "message": "请输入研究问题"})
            await websocket.close()
            return

        # 存用户消息
        user_message = Message(
            id=uuid.uuid4(),
            session_id=session.id,
            role=MessageRole.user,
            content=query,
        )
        db.add(user_message)
        await db.flush()
        


        # 通知前端开始
        await websocket.send_json({"type": "start", "message": "开始研究..."})

        # 流式跑 agent，每个节点完成后推送进度
        async for event in papyrus_graph.astream(
            {
                "query": query,
                "session_id": str(session.id),
                "user_id": str(user.id),
                "messages": [],
                "papers": [],
                "analysis": "",
                "report": "",
                "current_step": "",
                "error": None,
            },
            config={"callbacks": [get_langfuse_callback()]},
            stream_mode="updates",
        ):
            for node_name, node_output in event.items():
                step = node_output.get("current_step", "")
                messages = node_output.get("messages", [])

                # 推送进度消息
                for msg in messages:
                    await websocket.send_json({
                        "type": "progress",
                        "node": node_name,
                        "message": msg.content,
                    })

                # 如果是 writer 节点，推送最终报告
                if node_name == "writer":
                    report_content = node_output.get("report", "")
                    papers = node_output.get("papers", [])

                    report = Report(
                        id=uuid.uuid4(),
                        session_id=session.id,
                        user_id=user.id,
                        title=query[:100],
                        content={"markdown": report_content, "papers": papers},
                    )
                    db.add(report)
                    await db.flush()

                    # Ragas 评估
                    await evaluate_report(
                        db=db,
                        report_id=str(report.id),
                        query=query,
                        report_content=report_content,
                        papers=papers,
                    )

                    session.status = SessionStatus.done
                    session.title = query[:100]
                    await db.flush()

                    await websocket.send_json({
                        "type": "report",
                        "report": report_content,
                        "report_id": str(report.id),
                    })

        await websocket.send_json({"type": "done", "message": "研究完成！"})
        await db.commit()

    except WebSocketDisconnect:
        await db.rollback()
    except Exception as e:
        await db.rollback()
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass