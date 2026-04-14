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
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_json()
            query = data.get("query", "")
            session_id = data.get("sessionId")

            # Отправляем начальный статус
            await websocket.send_json({
                "type": "status",
                "status": "Определяю режим..."
            })

            # Проверка на пустой запрос
            if not query or not query.strip():
                await websocket.send_json({
                    "type": "error",
                    "status": "Запрос не может быть пустым"
                })
                continue

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
                    result_data = interpret_query(query, on_status=on_status, session_id=session_id)
                except Exception as e:
                    logger.error("Ошибка в interpret_query: %s", e)
                    error_data = str(e)

            # Запускаем interpret_query в отдельном потоке
            task = loop.run_in_executor(ThreadPoolExecutor(), run_interpret)

            # Параллельно слушаем очередь статусов
            while not task_done:
                try:
                    status_msg = await asyncio.wait_for(queue.get(), timeout=0.1)
                    await websocket.send_json(status_msg)
                except asyncio.TimeoutError:
                    if task.done():
                        task_done = True
                        if error_data:
                            await websocket.send_json({
                                "type": "error",
                                "status": f"Произошла ошибка: {error_data}"
                            })
                        break
                    continue

            if error_data:
                continue

            # Таймаут 30 секунд
            try:
                await asyncio.wait_for(task, timeout=30)
            except asyncio.TimeoutError:
                logger.error("Превышено время ожидания (30 сек) для запроса: %s", query[:100])
                await websocket.send_json({
                    "type": "error",
                    "status": "Превышено время ожидания (30 сек)"
                })
                continue

            # Отправляем результат
            if result_data:
                if result_data["mode"] == "consultation":
                    await websocket.send_json({
                        "type": "status",
                        "status": "Формирую ответ..."
                    })

                    consultation_answer = result_data.get("answer", "")
                    await websocket.send_json({
                        "type": "result",
                        "mode": "consultation",
                        "answer": consultation_answer,
                        "sessionId": session_id,
                    })

                    try:
                        save_exchange(session_id=session_id, user_query=query, mode="consultation", answer=consultation_answer)
                    except Exception as e:
                        logger.error("Ошибка сохранения истории: %s", e)
                elif result_data["mode"] == "clarification":
                    # Уточняющий вопрос — недостаточно данных для поиска
                    clarification_question = result_data.get("question", "")
                    await websocket.send_json({
                        "type": "result",
                        "mode": "clarification",
                        "question": clarification_question,
                        "sessionId": session_id,
                    })

                    try:
                        save_exchange(session_id=session_id, user_query=query, mode="clarification", answer=clarification_question)
                    except Exception as e:
                        logger.error("Ошибка сохранения истории: %s", e)
                else:
                    await websocket.send_json({
                        "type": "status",
                        "status": "Ищу на Reverb..."
                    })

                    await websocket.send_json({
                        "type": "status",
                        "status": "Ранжирую результаты..."
                    })

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

                    results_data = snake_to_camel([r.model_dump() for r in results])

                    from backend.agent.service import create_llm_client
                    from backend.agent.explanation import generate_explanation
                    llm_client_inst = create_llm_client()
                    explanation = generate_explanation(query, results_data, llm_client_inst)

                    await websocket.send_json({
                        "type": "result",
                        "mode": "search",
                        "results": results_data,
                        "explanation": explanation,
                        "sessionId": session_id,
                    })

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
