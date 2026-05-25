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


async def _handle_ui_action(websocket, action: dict, session_id, current_user) -> None:
    """Обрабатывает клик по UI-кнопке: исполняет search детерминированно, минуя router."""
    kind = action.get("kind")
    if kind != "search_with_budget":
        await websocket.send_json({"type": "error", "status": f"Неизвестное действие: {kind}"})
        return

    if not session_id:
        title = action.get("label") or "Search"
        session_id = create_session(title=str(title)[:100], user_id=current_user["id"])
    else:
        try:
            ensure_session_owner(int(session_id), current_user["id"])
            session_id = int(session_id)
        except (TypeError, ValueError, HTTPException):
            await websocket.send_json({"type": "error", "status": "Сессия не найдена"})
            return

    price_max = action.get("price_max")
    type_value = action.get("type") or "any"
    search_queries = list(action.get("search_queries") or [])

    try:
        from backend.search.search_reverb import search_reverb_exact
        from backend.ranking.ranking import rank_results
        from backend.models import GuitarResult
        from backend.agent.service import _build_empty_search_fallback, create_llm_client
        from backend.agent.explanation import generate_explanation

        raw = search_reverb_exact(search_queries, None, price_max, type=type_value)
        rank_params = {
            "budget_max": price_max,
            "search_queries": search_queries,
            "type": None if str(type_value).lower() == "any" else type_value,
        }
        try:
            ranked = rank_results(raw, rank_params)
        except Exception:
            ranked = raw[:5]

        results = [GuitarResult(
            id=str(item.get("id", "")),
            title=item.get("title", ""),
            price=float(item.get("price", 0)),
            currency=item.get("currency", "USD"),
            image_url=item.get("image_url", ""),
            listing_url=item.get("listing_url", ""),
        ) for item in ranked]
        results_data = snake_to_camel([r.model_dump(mode="json") for r in results])

        actions: list = []
        if results_data:
            llm_client = create_llm_client()
            user_query = action.get("label") or "Подбор по бюджету"
            explanation = generate_explanation(user_query, results_data, llm_client) if llm_client else ""
        else:
            params = {
                "search_queries": search_queries,
                "price_min": None,
                "price_max": price_max,
                "type": type_value,
            }
            explanation, actions = _build_empty_search_fallback(params, search_reverb_exact)

        search_params_data = snake_to_camel({
            "search_queries": search_queries,
            "price_min": None,
            "price_max": price_max,
            "type": type_value,
            "brand": None,
            "pickups": None,
            "sound": None,
            "style": None,
        })

        await websocket.send_json({
            "type": "result",
            "mode": "search",
            "results": results_data,
            "explanation": explanation,
            "searchParams": search_params_data,
            "sessionId": session_id,
            "actions": actions,
        })

        try:
            save_exchange(
                session_id=session_id,
                user_query=action.get("label") or "[action]",
                mode="search",
                answer=explanation or None,
                results=results_data,
                search_params=search_params_data,
            )
        except Exception as exc:
            logger.error("Ошибка сохранения action в историю: %s", exc)
    except Exception as exc:
        logger.exception("Ошибка обработки action: %s", exc)
        await websocket.send_json({"type": "error", "status": f"Ошибка: {exc}"})


def _save_error_exchange(session_id, query, error_text: str) -> None:
    """Сохраняет неудачный обмен в историю — чтобы при перезагрузке сессии было видно
    запрос пользователя и сообщение об ошибке вместо пустого диалога."""
    if not session_id or not query:
        return
    try:
        save_exchange(
            session_id=int(session_id),
            user_query=query,
            mode="error",
            answer=error_text,
        )
    except Exception as exc:
        logger.error("Не удалось сохранить error-обмен в историю: %s", exc)


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
            action = data.get("action")  # UI button click — детерминированный search без LLM

            # Action-сообщение: исполняем напрямую, минуя router
            if action and isinstance(action, dict):
                await _handle_ui_action(websocket, action, session_id, current_user)
                continue

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
                            error_text = error_data.get("status", "Произошла ошибка")
                            await websocket.send_json({
                                "type": "error",
                                "status": error_text
                            })
                            _save_error_exchange(session_id, query, error_text)
                        break
                    continue

            if error_data:
                continue

            # Таймаут 30 секунд
            try:
                await asyncio.wait_for(task, timeout=30)
            except asyncio.TimeoutError:
                logger.error("Превышено время ожидания (30 сек) для запроса: %s", query[:100])
                timeout_text = "Превышено время ожидания (30 сек)"
                await websocket.send_json({
                    "type": "error",
                    "status": timeout_text
                })
                _save_error_exchange(session_id, query, timeout_text)
                continue

            # Отправляем результат
            if result_data:
              try:
                if result_data["mode"] == "conversation":
                    await websocket.send_json({
                        "type": "status",
                        "status": "Формирую ответ..."
                    })

                    answer = result_data.get("answer", "")
                    await websocket.send_json({
                        "type": "result",
                        "mode": "conversation",
                        "answer": answer,
                        "debugThink": result_data.get("debug_think"),
                        "sessionId": session_id,
                    })
                    try:
                        record_exchange(
                            session_id,
                            "conversation",
                            elapsed_ms,
                            None,
                        )
                    except Exception as e:
                        logger.error("Ошибка записи метрик пайплайна: %s", e)

                    try:
                        save_exchange(session_id=session_id, user_query=query, mode="conversation", answer=answer)
                    except Exception as e:
                        logger.error("Ошибка сохранения истории: %s", e)
                elif result_data["mode"] == "consultation":
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

                    results_data = snake_to_camel([r.model_dump(mode="json") for r in results])

                    from backend.agent.service import create_llm_client
                    from backend.agent.explanation import generate_explanation
                    llm_client_inst = create_llm_client()
                    if results_data:
                        explanation = generate_explanation(query, results_data, llm_client_inst)
                    else:
                        # Backend-computed deterministic suggestion when nothing matched
                        explanation = result_data.get("fallback_explanation", "")

                    search_params = result_data.get("search_params")
                    search_params_data = snake_to_camel(search_params) if search_params else None

                    await websocket.send_json({
                        "type": "result",
                        "mode": "search",
                        "results": results_data,
                        "explanation": explanation,
                        "searchParams": search_params_data,
                        "sessionId": session_id,
                        "actions": result_data.get("actions") or [],
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
                            answer=explanation or None,
                            results=results_data,
                            search_params=search_params_data,
                        )
                    except Exception as e:
                        logger.error("Ошибка сохранения истории: %s", e)
              except WebSocketDisconnect:
                raise
              except Exception as exc:
                logger.exception("Ошибка при формировании/отправке результата: %s", exc)
                error_text = f"Произошла ошибка при формировании ответа: {exc}"
                try:
                    await websocket.send_json({
                        "type": "error",
                        "status": error_text,
                    })
                except Exception:
                    logger.error("Не удалось отправить ошибку клиенту")
                _save_error_exchange(session_id, query, error_text)
                continue

    except WebSocketDisconnect:
        logger.info("WebSocket клиент отключился")
    except Exception as e:
        logger.exception("Ошибка WebSocket: %s", e)
        try:
            await websocket.send_json({
                "type": "error",
                "status": f"Произошла ошибка: {str(e)}"
            })
        except Exception:
            logger.error("Не удалось отправить ошибку клиенту")
