import json

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.models import GuitarResult, WSMessage
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
async def chat(websocket: WebSocket):
    """WebSocket endpoint для чата с агентом."""
    await websocket.accept()

    try:
        # Отправляем начальный статус
        await websocket.send_json({
            "type": "status",
            "status": "Определяю режим..."
        })

        # Получаем сообщение от клиента
        data = await websocket.receive_json()
        query = data.get("query", "")

        # Проверка на пустой запрос
        if not query or not query.strip():
            await websocket.send_json({
                "type": "error",
                "status": "Запрос не может быть пустым"
            })
            return

        # Определяем режим и получаем результат
        result = interpret_query(query)

        if result["mode"] == "consultation":
            # Отправляем статус перед результатом
            await websocket.send_json({
                "type": "status",
                "status": "Формирую ответ..."
            })

            # Отправляем финальный результат
            await websocket.send_json({
                "type": "result",
                "mode": "consultation",
                "answer": result.get("answer", "")
            })
        else:
            # Search режим
            await websocket.send_json({
                "type": "status",
                "status": "Ищу на Reverb..."
            })

            await websocket.send_json({
                "type": "status",
                "status": "Ранжирую результаты..."
            })

            # Преобразуем результаты в формат GuitarResult
            results = []
            for item in result.get("results", []):
                results.append(GuitarResult(
                    id=str(item.get("id", "")),
                    title=item.get("title", ""),
                    price=float(item.get("price", 0)),
                    currency=item.get("currency", "USD"),
                    image_url=item.get("image_url", ""),
                    listing_url=item.get("listing_url", "")
                ))

            # Отправляем финальный результат
            await websocket.send_json({
                "type": "result",
                "mode": "search",
                "results": [r.model_dump() for r in results]
            })

    except WebSocketDisconnect:
        # Клиент отключился — это нормально
        pass
    except Exception as e:
        # Обрабатываем любые другие ошибки
        try:
            await websocket.send_json({
                "type": "error",
                "status": f"Произошла ошибка: {str(e)}"
            })
        except Exception:
            # Если не можем отправить ошибку — просто логируем
            pass
