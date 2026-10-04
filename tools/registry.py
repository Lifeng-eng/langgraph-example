from langgraph.graph import StateGraph, START, END,MessagesState
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage,ToolMessage,AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv(override=True)

llm = ChatDeepSeek(
    model="deepseek-v4-flash",
    extra_body={
        "thinking": {
        "type": "disabled"
    }
  }
)
@tool
def add(a: int, b: int) -> int:
    """计算两个整数的和。"""
    return a + b
tools = [add]
llm_with_tools = llm.bind_tools(tools)
tool_map = {t.name: t for t in tools}
print(tool_map)
print("==========================")
class AgentState(MessagesState):

    pass

def call_llm(state: AgentState) -> AgentState:
    response = llm_with_tools.invoke(state["messages"])
    print(response.tool_calls)
    return {"messages": [response]}
    from langchain_core.messages import AIMessage

def my_tools_condition(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "call_tools_custom"
    return END

    # 2. 自定义工具执行节点函数
def call_tools_custom(state: MessagesState) -> MessagesState:
    """手动遍历 tool_calls，执行对应函数，并返回 ToolMessage"""
    last_message = state["messages"][-1]
    tool_messages = []

    # 遍历 LLM 发起的所有工具调用请求（支持单次多工具调用）
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]

        print(f"正在执行工具: {tool_name}，参数: {tool_args}")

        # A. 查找并执行本地 Python 工具
        if tool_name in tool_map:
            tool_obj = tool_map[tool_name]
            # 执行工具获得返回值
            output = tool_obj.invoke(tool_args)
        else:
            output = f"错误：未找到名称为 {tool_name} 的工具。"

        # B. 将执行结果封装为 ToolMessage
        # ⚠️ 关键点：tool_call_id 必须与传入的 call_id 一致
        tool_msg = ToolMessage(
            content=str(output),
            tool_call_id=tool_call_id,
            name=tool_name
        )
        tool_messages.append(tool_msg)

    # C. 返回新增的 ToolMessage 列表，LangGraph 会自动追加到 state["messages"]
    return {"messages": tool_messages}
def main():
    graph = StateGraph(AgentState)
    graph.add_node("call_llm", call_llm)
    # 使用 ToolNode 自动处理工具调用
    graph.add_node("call_tools_custom", call_tools_custom)
    graph.add_edge(START, "call_llm")
    graph.add_conditional_edges("call_llm", my_tools_condition)
    graph.add_edge("call_tools_custom", "call_llm")
    app = graph.compile()
    result = app.invoke({"messages": [HumanMessage(content="请计算 123 + 456")]})
    print(result)
    print("===============================")
    print(result["messages"])
    print("==============================")
    print(result["messages"][1])
    print("==============================")
    print(result["messages"][1].content)
    for msg in result["messages"]:
            print(f"[{msg.__class__.__name__}]: {msg.content or msg.tool_calls}")
if __name__ == "__main__":
    main()
