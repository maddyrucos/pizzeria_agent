import json

from typing import Annotated, TypedDict, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from agent.tools import (
    create_delivery_order, book_table, search_knowledge_base
)


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
        elif name == "search_knowledge_base":
            out = search_knowledge_base.invoke(args)
        else:
            out = {"status": "error", "message": f"Unknown tool: {name}"}

        tool_messages.append(ToolMessage(content=json.dumps(out, ensure_ascii=False), tool_call_id=call["id"]))

    return {"messages": tool_messages}


def build_app():
    g = StateGraph(AgentState)
    g.add_node("llm", llm_node)
    g.add_node("tools", tools_node)

    g.set_entry_point("llm")
    g.add_conditional_edges("llm", route_after_llm, {"tools": "tools", "end": END})
    g.add_edge("tools", "llm")  # после tool -> обратно в LLM для финального текста

    return g.compile()


def main(state: AgentState) -> AgentState:
    app = build_app()
    return app.invoke({"messages": state["messages"] + [HumanMessage(content=user)]}, config=None)



if __name__ == "__main__":
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
        
        state["messages"] + [HumanMessage(content=user)]
        
        state = main(state)
        for msg in state["messages"][-1:]:
            if isinstance(msg, AIMessage):
                print("Ассистент:", msg.content)
