from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from pydantic.alias_generators import to_camel
from typing import Optional, List, Literal

class ChatRequest(BaseModel):
    """Модель запроса к chat API."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    # Валидация: от 2 до 500 символов
    query: str = Field(..., min_length=2, max_length=500, description="Текстовый запрос пользователя")


class GuitarResult(BaseModel):
    """Модель результата поиска (одна гитара)."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: Optional[str] = Field(None, description="Уникальный ID объявления")
    title: str = Field(..., description="Название гитары")
    
    # Валидация: цена от 0 до 100 000
    price: float = Field(..., ge=0, le=100000, description="Цена лота")
    
    # Валидация: только список разрешенных валют
    currency: Literal["USD", "EUR", "GBP", "RUB", "JPY"] = Field(default="USD")
    
    # Валидация: строгая проверка URL
    listing_url: HttpUrl = Field(..., description="Ссылка на страницу товара")
    image_url: Optional[HttpUrl] = Field(None, description="Ссылка на изображение")


SearchResult = GuitarResult


class SearchParams(BaseModel):
    """LLM-derived параметры поиска, показываемые пользователю."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    search_queries: List[str] = Field(default_factory=list)
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    type: Optional[str] = None
    brand: Optional[str] = None
    pickups: Optional[str] = None
    sound: Optional[str] = None
    style: Optional[str] = None


class ChatResponse(BaseModel):
    """Модель ответа от chat API."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    # Валидация: только конкретные режимы
    mode: Literal["search", "consultation", "clarification"]
    results: Optional[List[GuitarResult]] = Field(default=None, description="Результаты поиска")
    answer: Optional[str] = Field(default=None, description="Текстовый ответ LLM")
    debug_think: Optional[str] = Field(default=None, description="Служебные рассуждения LLM для dev UI")
    question: Optional[str] = Field(default=None, description="Уточняющий вопрос")
    search_params: Optional[SearchParams] = Field(default=None, description="Параметры поиска из LLM-router")
