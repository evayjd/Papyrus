import asyncio
import websockets
import json

async def test():
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/auth/login",
            json={"email": "test@test.com", "password": "123456"}
        )
        token = response.json()["access_token"]
        print(f"登录成功，token: {token[:20]}...")

        # 创建 session
        response = await client.post(
            "http://localhost:8000/sessions/",
            json={"title": "测试研究"},
            headers={"Authorization": f"Bearer {token}"}
        )
        session_id = response.json()["id"]
        print(f"创建 session: {session_id}")

    uri = f"ws://localhost:8000/research/ws/{session_id}"
    async with websockets.connect(uri, ping_timeout=300) as ws:
        # 发送 token
        await ws.send(json.dumps({"token": token}))

        await ws.send(json.dumps({"query": "RAG retrieval augmented generation"}))

        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"[{data['type']}] {data.get('message', '')[:100]}")
            if data["type"] in ["done", "error"]:
                break

asyncio.run(test())