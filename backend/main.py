import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.models import GuitarResult, WSMessage
from backend.agent.service import interpret_query
from backend.search.router import router as chat_router
from backend.history.router import router as history_router
from backend.history.service import init_db, save_exchange, create_session
from backend.utils.logger import get_logger
from backend.utils.serializer import snake_to_camel

logger = get_logger("main")

app = FastAPI(title="Guitar Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(history_router)


@app.on_event("startup")
def startup():
    init_db()


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
        session_id = data.get("sessionId")

        # Проверка на пустой запрос
        if not query or not query.strip():
            await websocket.send_json({
                "type": "error",
                "status": "Запрос не может быть пустым"
            })
            return

        # Создаём сессию, если не передана
        if not session_id:
            session_id = create_session(title=query[:100])

        # Создаём очередь для статусов
        queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        # Флаги и данные для результата
        task_done = False
        result_data = None
        error_data = None

        def on_status(text: str):
            """Callback для отправки статусов из синхронного кода."""
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"type": "status", "status": text}
            )

        # Функция для запуска в потоке
        def run_interpret():
            nonlocal result_data, error_data
            try:
                logger.info("WebSocket запрос: %s", query[:100])
                result_data = interpret_query(query, on_status=on_status)
            except Exception as e:
                logger.error("Ошибка в interpret_query: %s", e)
                error_data = str(e)

        # Запускаем interpret_query в отдельном потоке
        task = loop.run_in_executor(ThreadPoolExecutor(), run_interpret)

        # Параллельно слушаем очередь статусов
        while not task_done:
            try:
                # Ждём либо статус, либо завершение задачи
                status_msg = await asyncio.wait_for(queue.get(), timeout=0.1)
                await websocket.send_json(status_msg)
            except asyncio.TimeoutError:
                # Проверяем завершение задачи
                if task.done():
                    task_done = True
                    # Проверяем результат
                    if error_data:
                        await websocket.send_json({
                            "type": "error",
                            "status": f"Произошла ошибка: {error_data}"
                        })
                        return
                    break
                continue

        # Добавляем таймаут 30 секунд на выполнение
        try:
            await asyncio.wait_for(task, timeout=30)
        except asyncio.TimeoutError:
            logger.error("Превышено время ожидания (30 сек) для запроса: %s", query[:100])
            await websocket.send_json({
                "type": "error",
                "status": "Превышено время ожидания (30 сек)"
            })
            return

        # Отправляем результат
        if result_data:
            if result_data["mode"] == "consultation":
                await websocket.send_json({
                    "type": "status",
                    "status": "Формирую ответ..."
                })

                # Отправляем финальный результат
                consultation_answer = result_data.get("answer", "")
                await websocket.send_json({
                    "type": "result",
                    "mode": "consultation",
                    "answer": consultation_answer,
                    "sessionId": session_id,
                })

                # Сохраняем в историю
                try:
                    save_exchange(session_id=session_id, user_query=query, mode="consultation", answer=consultation_answer)
                except Exception as e:
                    logger.error("Ошибка сохранения истории: %s", e)
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
                for item in result_data.get("results", []):
                    results.append(GuitarResult(
                        id=str(item.get("id", "")),
                        title=item.get("title", ""),
                        price=float(item.get("price", 0)),
                        currency=item.get("currency", "USD"),
                        image_url=item.get("image_url", ""),
                        listing_url=item.get("listing_url", "")
                    ))

                # Преобразуем snake_case в camelCase перед отправкой
                results_data = snake_to_camel([r.model_dump() for r in results])

                # Отправляем финальный результат
                await websocket.send_json({
                    "type": "result",
                    "mode": "search",
                    "results": results_data,
                    "sessionId": session_id,
                })

                # Сохраняем в историю
                try:
                    save_exchange(session_id=session_id, user_query=query, mode="search", results=results_data)
                except Exception as e:
                    logger.error("Ошибка сохранения истории: %s", e)

    except WebSocketDisconnect:
        logger.info("WebSocket клиент отключился")
    except Exception as e:
        logger.error("Ошибка WebSocket: %s", e)
        try:
            await websocket.send_json({
                "type": "error",
                "status": f"Произошла ошибка: {str(e)}"
            })
        except Exception:
            logger.error("Не удалось отправить ошибку клиенту")
