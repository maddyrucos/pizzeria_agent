from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Annotated, TypedDict, List

from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages


# ----------------------------
# Tools (заглушки бизнес-логики)
# ----------------------------

class DeliveryOrderIn(BaseModel):
    pizza_name: str = Field(..., description="Название пиццы (как у пользователя)")
    address: str = Field(..., description="Адрес доставки одной строкой")


class TableBookingIn(BaseModel):
    time: str = Field(..., description="Время брони (как у пользователя: '19:30', 'завтра 18:00' и т.п.)")
    name: str = Field(..., description="Имя бронирующего")


@tool("create_delivery_order", args_schema=DeliveryOrderIn, description="Оформить заказ на доставку пиццы")
def create_delivery_order(pizza_name: str, address: str) -> dict:
    """Оформить заказ на доставку (заглушка)."""
    # Тут обычно: создание заказа в БД / вызов сервиса / очереди и т.п.
    return {"status": "ok", "order_id": "ord_stub_001", "pizza_name": pizza_name, "address": address}


@tool("book_table", args_schema=TableBookingIn, description="Забронировать столик в пиццерии")
def book_table(time: str, name: str) -> dict:
    """Забронировать столик (заглушка)."""
    return {"status": "ok", "booking_id": "bk_stub_001", "time": time, "name": name}


TOOLS = [create_delivery_order, book_table]


# ----------------------------
# Retrieval-augmented knowledge base
# ----------------------------

class KnowledgeSearchInput(BaseModel):
    query: str = Field(..., description="Вопрос или ключевые слова для поиска по меню и отзывам")


def _load_documents() -> List[Document]:
    """
    Собираем документы из CSV меню и отзывов, чтобы раздать их в Chroma.
    """
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = root_dir / "data"

    documents: List[Document] = []

    menu_path = data_dir / "pizzeria_menu.csv"
    if menu_path.exists():
        with menu_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name", "").strip()
                category = row.get("category", "").strip()
                description = row.get("description", "").strip()
                price = row.get("price_usd", "").strip()

                content = (
                    f"Menu item: {name} (category: {category}). "
                    f"Description: {description}. Price: ${price} USD."
                )
                documents.append(
                    Document(
                        page_content=content,
                        metadata={
                            "source": "menu",
                            "name": name,
                            "category": category,
                            "price": price,
                        },
                    )
                )

    reviews_path = data_dir / "restaurant_reviews.csv"
    if reviews_path.exists():
        with reviews_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row.get("Title", "").strip()
                date = row.get("Date", "").strip()
                rating = row.get("Rating", "").strip()
                review_text = row.get("Review", "").strip()

                content = (
                    f"Review titled '{title}' on {date} rated {rating}/5: {review_text}"
                )
                documents.append(
                    Document(
                        page_content=content,
                        metadata={
                            "source": "review",
                            "title": title,
                            "date": date,
                            "rating": rating,
                        },
                    )
                )

    return documents


_retriever = None


def _build_retriever():
    global _retriever
    if _retriever is not None:
        return _retriever

    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    persist_dir = str(Path(__file__).resolve().parent.parent / "chroma_db")

    vectorstore = Chroma.from_documents(
        _load_documents(),
        embedding=embeddings,
        collection_name="pizzeria-knowledge",
        persist_directory=persist_dir,
    )
    _retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    return _retriever


@tool(
    "search_knowledge_base",
    args_schema=KnowledgeSearchInput,
    description=(
        "Поиск по базе знаний меню и отзывов. Используй это, когда нужно ответить на "
        "вопросы про блюда, цены, состав, популярные позиции, ожидание доставки или впечатления гостей."
    ),
)
def search_knowledge_base(query: str) -> dict:
    retriever = _build_retriever()
    docs = retriever.invoke(query)

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


TOOLS = [create_delivery_order, book_table, search_knowledge_base]


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


SYSTEM_PROMPT = """
You are a pizzeria assistant. This is a single establishment, not a chain.
Your task is to help the user either place a home delivery pizza order OR reserve a table (only one action at a time!). You can also answer the user’s questions.

You have access to a knowledge base with menu items and recent customer reviews. When users ask about ingredients, prices, recommendations, delivery expectations, or guest experiences, first call the tool `search_knowledge_base(query)` to ground your answer in real data.

Rules:

1. If the user requests home delivery, call the tool `create_delivery_order(pizza_name, address)`. Return the order number exactly as written in `id`.
   If required data is missing (pizza name or address), ask a clarifying question.
2. If the user requests a reservation, call the tool `book_table(time, name)`. Return the reservation number exactly as written in `id`.
   If required data is missing (time or name), ask a clarifying question.
3. If the user asks about menu items, prices, availability, popular choices, or feedback from visitors, call `search_knowledge_base` with a concise query. Use the retrieved facts in your reply.
4. Do not invent data: if something is missing, ask for it.
5. After calling the tool, briefly confirm the result to the user (you may show the `id`).

IMPORTANT:

* NEVER call a tool if the user request is unclear.
* NEVER call a tool with empty or assumed arguments.
* If data is missing or the input is unclear, ask a clarifying question in plain text.
"""


# ----------------------------
# Nodes
# ----------------------------

def llm_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(
        model="Qwen/Qwen2.5-3B-Instruct",
        base_url="http://localhost:8000/v1",
        api_key="EMPTY",
        temperature=0,
    ).bind_tools(TOOLS)

    msgs = state["messages"]
    if not msgs or not isinstance(msgs[0], SystemMessage):
        msgs = [SystemMessage(content=SYSTEM_PROMPT)] + msgs

    resp = llm.invoke(msgs)

    return {"messages": [resp]}

def route_after_llm(state):
    last = state["messages"][-1]

    if not isinstance(last, AIMessage):
        return "end"

    if not last.tool_calls:
        return "end"

    
    call = last.tool_calls[0]
    args = call.get("args") or {}

    # защита от пустых аргументов
    if any(not v or not str(v).strip() for v in args.values()):
        return "end"

    return "tools"



def tools_node(state: AgentState) -> AgentState:
    """
    Исполняем все tool_calls, добавляем ToolMessage(и) в историю.
    """
    last = state["messages"][-1]
    assert isinstance(last, AIMessage)

    tool_messages: List[ToolMessage] = []
    for call in last.tool_calls:
        name = call["name"]
        args = call.get("args", {}) or {}

        if name == "create_delivery_order":
            out = create_delivery_order.invoke(args)
        elif name == "book_table":
            out = book_table.invoke(args)
        else:
            out = {"status": "error", "message": f"Unknown tool: {name}"}

        tool_messages.append(ToolMessage(content=str(out), tool_call_id=call["id"]))

    return {"messages": tool_messages}


# ----------------------------
# Build graph
# ----------------------------

def build_app():
    g = StateGraph(AgentState)
    g.add_node("llm", llm_node)
    g.add_node("tools", tools_node)

    g.set_entry_point("llm")
    g.add_conditional_edges("llm", route_after_llm, {"tools": "tools", "end": END})
    g.add_edge("tools", "llm")  # после tool -> обратно в LLM для финального текста

    return g.compile()


# ----------------------------
# CLI demo
# ----------------------------

def main():
    app = build_app()
    state: AgentState = {"messages": []}

    while True:
        try:
            user = input("Вы: ").strip()
        except EOFError:
            break
        if not user:
            continue
        if user.lower() in {"exit", "quit"}:
            break

        state = app.invoke({"messages": state["messages"] + [HumanMessage(content=user)]}, config=None)
        # app.invoke возвращает только новый state; для продолжения диалога сохраняем его
        # (в данном простом примере state уже содержит историю из add_messages)

        

        # Печатаем последнее человекочитаемое сообщение ассистента (не tool)
        # Обычно это будет последний AIMessage без tool_calls.
        # for msg in (state["messages"]):
        #     print(f'DEBUG: msg type: {type(msg)}, content: {msg.content}, tool_calls: {getattr(msg, "tool_calls", None)}')
        
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
                print("Агент:", msg.content)
                break


if __name__ == "__main__":
    main()
