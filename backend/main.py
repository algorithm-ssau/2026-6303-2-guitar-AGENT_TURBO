import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.service import interpret_query
from backend.search.router import router as chat_router

app = FastAPI(title="Guitar Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/")
def root():
    return {"status": "ok"}


@app.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket-эндпоинт для чата с агентом.

    Принимает: {"query": "текст запроса"}
    Отправляет:
      - {"type": "status", "text": "..."} — промежуточные статусы
      - {"type": "result", "mode": "search", "results": [...]} — результат поиска
      - {"type": "result", "mode": "consultation", "answer": "..."} — консультация
      - {"type": "error", "text": "..."} — ошибка
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            query = data.get("query", "").strip()

            if not query:
                await websocket.send_json({"type": "error", "text": "Пустой запрос"})
                continue

            # Callback для отправки статусов через WebSocket
            async def send_status(text: str):
                await websocket.send_json({"type": "status", "text": text})

            # Собираем статусы синхронно, потом отправляем
            statuses = []

            def on_status(text: str):
                statuses.append(text)

            result = interpret_query(text=query, on_status=on_status)

            # Отправляем все собранные статусы
            for status_text in statuses:
                await websocket.send_json({"type": "status", "text": status_text})

            # Отправляем финальный результат
            response = {"type": "result", "mode": result.get("mode", "consultation")}
            if result.get("mode") == "search":
                response["results"] = result.get("results", [])
            else:
                response["answer"] = result.get("answer", "")

            await websocket.send_json(response)

    except WebSocketDisconnect:
        pass
