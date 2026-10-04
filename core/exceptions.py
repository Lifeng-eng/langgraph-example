from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.postgres import PostgresSaver  # 1. 正确导入 PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import MessagesState
from psycopg_pool import ConnectionPool  # 2. 导入连接池

load_dotenv(override=True)

# 1. 初始化模型
model = ChatDeepSeek(
    model="deepseek-v4-flash",
    extra_body={
        "thinking": {
            "type": "disabled"
        }
    }
)


# 2. 定义状态
class OverAllState(MessagesState):
    output: str


# 3. 定义节点
def llm_node(state: OverAllState) -> OverAllState:
    messages = state["messages"]
    res = model.invoke(messages)
    return {
        "messages": [res]
    }


def output_node(state: OverAllState) -> OverAllState:
    return {
        "output": state["messages"][-1].content
    }


# 4. 构建图
builder = StateGraph(state_schema=OverAllState)
builder.add_node("llm_node", llm_node)
builder.add_node("output_node", output_node)
builder.add_edge(START, "llm_node")
builder.add_edge("llm_node", "output_node")
builder.add_edge("output_node", END)

# 5. 数据库连接与 Checkpointer 配置
# 注意：psycopg3 驱动的 URI 格式为 postgresql://...
DB_URI = "postgresql://langgraph_user:123456@localhost:5432/langgraph_db"

# 使用 ConnectionPool 管理数据库连接
with ConnectionPool(conninfo=DB_URI, max_size=20, kwargs={"autocommit": True}) as pool:
    checkpointer = PostgresSaver(pool)
    
    # 首次运行时自动在数据库中创建表结构（如 checkpoints 表）
    checkpointer.setup()
    
    # 编译图并绑定 checkpointer
    graph = builder.compile(checkpointer=checkpointer)
    
    # 配置 thread_id 保持会话
    config = {"configurable": {"thread_id": "chapter_6_6_2_4"}}
    
    # 多轮对话测试
    graph.invoke({"messages": [HumanMessage("你好，我是老王")]}, config=config)
    graph.invoke({"messages": [HumanMessage("从现在开始，你是小王")]}, config=config)
    
    res = graph.invoke({"messages": [HumanMessage("我是谁?你是谁?")]}, config=config)
    
    # 打印最终节点的 output 字段输出
    print("=== output 节点结果 ===")
    print(res["output"])
    
    # 正确遍历消息历史（messages 列表里的元素是 BaseMessage 对象，包含 .content 属性）
    print("\n=== 完整对话历史 ===")
    for msg in res["messages"]:
        print(f"[{msg.type}]: {msg.content}")