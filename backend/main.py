from fastapi import FastAPI
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, AIMessage

from agent.main import build_app

app = FastAPI()

CHATS = {} # временное хранилище состояний чатов

class UserRequest(BaseModel):
    message: list
    user_id: str

@app.post("/agent")
async def agent_endpoint(request: UserRequest):
    user_id = request.user_id
    state = CHATS.get(user_id, {"messages": []})

    state = build_app().invoke({"messages": state["messages"] + [HumanMessage(content=msg) for msg in request.message]}, config=None)

    CHATS[user_id] = state

    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage):
        return {"response": last_message.content}
    else:
        return {"response": "No response from agent."}