import asyncio
import importlib
import json
import time
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.models import GuitarResult, WSMessage
from backend.agent.service import InvalidRouterResponseError, LLMUnavailableError, interpret_query
from backend.auth.service import init_auth_db, verify_token
from backend.history.service import ensure_session_owner, init_db, save_exchange, create_session
from backend.analytics.pipeline_metrics import record_exchange
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

ROUTER_MODULES = ["auth", "search", "history", "analytics", "feedback", "health"]
for name in ROUTER_MODULES:
    try:
        mod = importlib.import_module(f"backend.{name}.router")
        if hasattr(mod, "router"):
            app.include_router(mod.router)
            logger.info("Loaded router: %s", name)
    except ImportError as e:
        logger.warning("Router %s not available: %s", name, e)


@app.on_event("startup")
def startup():
    init_db()
    init_auth_db()


@app.get("/")
def root():
    return {"status": "ok"}


@app.websocket("/chat")
async def chat(websocket: WebSocket):
    """WebSocket endpoint для чата с агентом."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        current_user = verify_token(token)
    except HTTPException:
        await websocket.close(code=1008)
        return

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
                session_id = create_session(title=query[:100], user_id=current_user["id"])
            else:
                try:
                    ensure_session_owner(int(session_id), current_user["id"])
                    session_id = int(session_id)
                except (TypeError, ValueError, HTTPException):
                    await websocket.send_json({
                        "type": "error",
                        "status": "Сессия не найдена"
                    })
                    continue

            # Создаём очередь для статусов
            queue = asyncio.Queue()
            loop = asyncio.get_event_loop()

            # Флаги и данные для результата
            task_done = False
            result_data = None
            error_data = None
            elapsed_ms = 0

            def on_status(text: str):
                """Callback для отправки статусов из синхронного кода."""
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    {"type": "status", "status": text}
                )

            # Функция для запуска в потоке
            def run_interpret():
                nonlocal result_data, error_data, elapsed_ms
                try:
                    logger.info("WebSocket запрос: %s", query[:100])
                    t0 = time.perf_counter()
                    result_data = interpret_query(query, on_status=on_status, session_id=session_id)
                    elapsed_ms = int((time.perf_counter() - t0) * 1000)
                except LLMUnavailableError as e:
                    logger.error("LLM недоступна в interpret_query: %s", e)
                    error_data = {
                        "status": e.user_message,
                    }
                except InvalidRouterResponseError as e:
                    logger.error("Некорректный ответ LLM-router: %s", e)
                    error_data = {
                        "status": "Сервис временно недоступен: LLM-router вернул некорректный ответ.",
                    }
                except Exception as e:
                    logger.error("Ошибка в interpret_query: %s", e)
                    error_data = {"status": f"Произошла ошибка: {str(e)}"}

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
                                "status": error_data.get("status", "Произошла ошибка")
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

                    answer = result_data.get("answer", "")
                    await websocket.send_json({
                        "type": "result",
                        "mode": "consultation",
                        "answer": answer,
                        "debugThink": result_data.get("debug_think"),
                        "sessionId": session_id,
                    })
                    try:
                        record_exchange(
                            session_id,
                            result_data["mode"],
                            elapsed_ms,
                            None,
                        )
                    except Exception as e:
                        logger.error("Ошибка записи метрик пайплайна: %s", e)

                    try:
                        save_exchange(session_id=session_id, user_query=query, mode="consultation", answer=answer)
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
                        record_exchange(
                            session_id,
                            result_data["mode"],
                            elapsed_ms,
                            None,
                        )
                    except Exception as e:
                        logger.error("Ошибка записи метрик пайплайна: %s", e)

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

                    search_params = result_data.get("search_params")
                    search_params_data = snake_to_camel(search_params) if search_params else None

                    await websocket.send_json({
                        "type": "result",
                        "mode": "search",
                        "results": results_data,
                        "explanation": explanation,
                        "searchParams": search_params_data,
                        "sessionId": session_id,
                    })
                    try:
                        record_exchange(
                            session_id,
                            result_data["mode"],
                            elapsed_ms,
                            len(result_data.get("results", [])),
                        )
                    except Exception as e:
                        logger.error("Ошибка записи метрик пайплайна: %s", e)

                    try:
                        save_exchange(
                            session_id=session_id,
                            user_query=query,
                            mode="search",
                            results=results_data,
                            search_params=search_params_data,
                        )
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
