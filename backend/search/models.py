from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, List


class ChatRequest(BaseModel):
    """Модель запроса к chat API."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    query: str = Field(..., min_length=1, description="Текстовый запрос пользователя")


class SearchResult(BaseModel):
    """Модель результата поиска."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: str = Field(..., description="Уникальный ID объявления")
    title: str = Field(..., description="Название гитары")
    price: float = Field(..., description="Цена лота")
    currency: str = Field(default="USD", description="Валюта (всегда USD)")
    image_url: str = Field(..., description="Ссылка на изображение")
    listing_url: str = Field(..., description="Ссылка на страницу товара")


class ChatResponse(BaseModel):
    """Модель ответа от chat API."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    mode: str = Field(..., description="Режим ответа: 'search' или 'consultation'")
    results: Optional[List[SearchResult]] = Field(default=None, description="Результаты поиска")
    answer: Optional[str] = Field(default=None, description="Текстовый ответ LLM")
