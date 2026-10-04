from langgraph.store.memory import InMemoryStore
from typing import TypedDict
from langgraph.runtime import Runtime
from langgraph.graph import StateGraph, END, START

store = InMemoryStore()


class State(TypedDict):
    user_input: str

namespace = ("users","user_001","memories")

store.put(
    namespace,
    "profile",
    {
        "name": "小明",
        "job": "Java Developer",
        "language": "Python"
    }
)
def memory_node(state: State,runtime: Runtime):

    memory = runtime.store.get(
        namespace,
        "profile"
    )
    if memory:
        print("读取长期记忆")
        print(memory)
        print("-------------------")
        print(memory.value)

    return {}
builder = StateGraph(State)
builder.add_node("memory", memory_node)
builder.add_edge(START, "memory")
builder.add_edge("memory", END)
graph = builder.compile(store=store)
graph.invoke({"user_input": "你好"})
