from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """Модель запроса к chat API."""
    query: str = Field(..., description="Текстовый запрос пользователя")


class SearchResult(BaseModel):
    """Модель результата поиска."""
    id: str = Field(..., description="Уникальный ID объявления")
    title: str = Field(..., description="Название гитары")
    price: float = Field(..., description="Цена лота")
    currency: str = Field(default="USD", description="Валюта (всегда USD)")
    image_url: str = Field(..., description="Ссылка на изображение")
    listing_url: str = Field(..., description="Ссылка на страницу товара")


class ChatResponse(BaseModel):
    """Модель ответа от chat API."""
    mode: str = Field(..., description="Режим ответа: 'search' или 'chat'")
    results: Optional[List[SearchResult]] = Field(default=None, description="Результаты поиска")
    answer: Optional[str] = Field(default=None, description="Текстовый ответ LLM")
