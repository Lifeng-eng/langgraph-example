from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore


# 定义状态

class State(TypedDict):
    messages: list
    response: str

store = InMemoryStore()

namespace = ("users", "user_001", "memories")

store.put(
    namespace,
    "tech_stack",
    {
        "text": "我是 Java 后端开发者"
    }
)

store.put(
    namespace,
    "habit",
    {
        "text": "我喜欢晚上学习"
    }
)

store.put(
    namespace,
    "food",
    {
        "text": "我喜欢吃面"
    }
)

def memory_node(state:State,runtime:Runtime[Context]) -> dict:

    #拿到最后一条消息
    message = state["messages"][-1]
    namespace = ("users", "user_001", "memories")

    memorys = runtime.store.search(namespace)

    user_memories = [m.value for m in memorys]

    print(user_memories)

    return {"response": user_memories}
