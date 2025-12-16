from __future__ import annotations

import json
from typing import Annotated, Literal, Optional, TypedDict, List

from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

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


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


SYSTEM_PROMPT = """
You are a pizzeria assistant. This is a single establishment, not a chain.
Your task is to help the user either place a home delivery pizza order OR reserve a table (only one action at a time!). You can also answer the user’s questions.

Rules:

1. If the user requests home delivery, call the tool `create_delivery_order(pizza_name, address)`. Return the order number exactly as written in `id`.
   If required data is missing (pizza name or address), ask a clarifying question.
2. If the user requests a reservation, call the tool `book_table(time, name)`. Return the reservation number exactly as written in `id`.
   If required data is missing (time or name), ask a clarifying question.
3. Do not invent data: if something is missing, ask for it.
4. After calling the tool, briefly confirm the result to the user (you may show the `id`).

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
