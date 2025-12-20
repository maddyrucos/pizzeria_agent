from langchain_core.tools import tool
from pydantic import BaseModel, Field

from agent.rag import RAG


class DeliveryOrderIn(BaseModel):
    pizza_name: str = Field(..., description="Название пиццы (как у пользователя)")
    address: str = Field(..., description="Адрес доставки одной строкой")

@tool("create_delivery_order", args_schema=DeliveryOrderIn, description="Оформить заказ на доставку пиццы")
def create_delivery_order(pizza_name: str, address: str) -> dict:
    """Оформить заказ на доставку (заглушка)."""
    # Тут обычно: создание заказа в БД / вызов сервиса / очереди и т.п.
    return {"status": "ok", "order_id": "ord_stub_001", "pizza_name": pizza_name, "address": address}


class TableBookingIn(BaseModel):
    time: str = Field(..., description="Время брони (как у пользователя: '19:30', 'завтра 18:00' и т.п.)")
    name: str = Field(..., description="Имя бронирующего")

@tool("book_table", args_schema=TableBookingIn, description="Забронировать столик в пиццерии")
def book_table(time: str, name: str) -> dict:
    """Забронировать столик (заглушка)."""
    return {"status": "ok", "booking_id": "bk_stub_001", "time": time, "name": name}


class KnowledgeSearchInput(BaseModel):
    query: str = Field(..., description="Вопрос или ключевые слова для поиска по меню и отзывам")

@tool(
    "search_knowledge_base",
    args_schema=KnowledgeSearchInput,
    description=(
        "Поиск по базе знаний меню и отзывов. Используй это, когда нужно ответить на "
        "вопросы про блюда, цены, состав, популярные позиции, ожидание доставки или впечатления гостей."
    ),
)
def search_knowledge_base(query: str) -> dict:
    rag = RAG()
    docs = rag.retriever.invoke(query)

    results = []
    for doc in docs:
        source = doc.metadata.get("source")
        if source == "menu":
            results.append(
                {
                    "type": "menu",
                    "name": doc.metadata.get("name"),
                    "category": doc.metadata.get("category"),
                    "price_usd": doc.metadata.get("price"),
                    "detail": doc.page_content,
                }
            )
        else:
            results.append(
                {
                    "type": "review",
                    "title": doc.metadata.get("title"),
                    "date": doc.metadata.get("date"),
                    "rating": doc.metadata.get("rating"),
                    "detail": doc.page_content,
                }
            )

    return {"matches": results}