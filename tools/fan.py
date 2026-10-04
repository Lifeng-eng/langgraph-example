from typing import Any, Annotated, TypedDict
from operator import add

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send


# 1. 定义状态：results 用 add 合并，模拟“扇入”时多个结果累加
class State(TypedDict):
    number: int
    results: Annotated[list[str], add]


# 2. 三个并行的分支节点（扇出的目标）
def plus_one(state: State) -> dict[str, Any]:
    return {"results": [f"+1 = {state['number'] + 1}"]}


def times_two(state: State) -> dict[str, Any]:
    return {"results": [f"x2 = {state['number'] * 2}"]}


def minus_three(state: State) -> dict[str, Any]:
    return {"results": [f"-3 = {state['number'] - 3}"]}


# 3. 扇出（条件路由函数）：返回多个 Send，让它们并行执行
#    注意：这个函数只能作为 add_conditional_edges 的路由函数，不能作为 add_node 的节点
def fan_out(state: State):
    return [
        Send("plus_one", state),
        Send("times_two", state),
        Send("minus_three", state),
    ]


# 可选：一个“标记/预处理”节点，让图从 START 先进入这里，再扇出
def start_node(state: State) -> dict[str, Any]:
    # 这里可以对 state 做预处理，或什么都不做
    return {}


# 4. 扇入：合并所有分支的结果
def merge(state: State) -> dict[str, Any]:
    return {"results": [" >> ".join(state["results"])]}


# 5. 组装图
graph = StateGraph(State)
graph.add_node("start_node", start_node)
graph.add_node("plus_one", plus_one)
graph.add_node("times_two", times_two)
graph.add_node("minus_three", minus_three)
graph.add_node("merge", merge)

graph.add_edge(START, "start_node")
# 关键：从 start_node 出发，用 fan_out（条件路由函数）扇出到多个节点
graph.add_conditional_edges("start_node", fan_out, ["plus_one", "times_two", "minus_three"])
# 三个分支都汇聚到 merge
graph.add_edge("plus_one", "merge")
graph.add_edge("times_two", "merge")
graph.add_edge("minus_three", "merge")
graph.add_edge("merge", END)

app = graph.compile()

result = app.invoke({"number": 10, "results": []})
print(result)
# 输出 results 会是类似：['+1 = 11', 'x2 = 20', '-3 = 7', '+1 = 11 >> x2 = 20 >> -3 = 7']
