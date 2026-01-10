from langchain_core.messages import HumanMessage, AIMessage


class Serializer:
    def serialize_messages(self, messages: list) -> list[dict]:
        result = []
        for m in messages:
            if isinstance(m, HumanMessage):
                role = "human" 
            elif isinstance(m, AIMessage):
                role = "ai"
            else:
                continue

            result.append(
                {
                    "role": role,
                    "content": m.content,
                }
            )
        return result


    def deserialize_messages(self, data: list[dict]) -> list:
        result = []
        for item in data:
            if item["role"] == "human":
                result.append(HumanMessage(content=item["content"]))
            elif item["role"] == "ai":
                result.append(AIMessage(content=item["content"]))
        return result