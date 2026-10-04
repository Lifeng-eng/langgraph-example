import asyncio

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_community.embeddings import DashScopeEmbeddings

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.store.postgres import AsyncPostgresStore, PoolConfig


load_dotenv(override=True)


DB_URI = "postgresql://langgraph_user:123456@localhost:5432/langgraph_db"


# ============================================================
# Embedding
# ============================================================

embeddings = DashScopeEmbeddings(
    model="qwen3.7-text-embedding-flash"
)


def get_vector(text: str) -> list[float]:
    return embeddings.embed_query(text)


# ============================================================
# Main
# ============================================================

async def main():

    # --------------------------------------------------------
    # 测试 Embedding
    # --------------------------------------------------------

    test_vec = get_vector("测试一下")

    print("Embedding 类型:", type(test_vec))
    print("Embedding 维度:", len(test_vec))
    print("前 5 个向量:", test_vec[:5])

    if len(test_vec) != 1024:
        raise ValueError(
            f"Embedding 维度不是 1024，而是 {len(test_vec)}"
        )

    print("✅ Embedding 测试通过")


    # --------------------------------------------------------
    # 创建 AsyncPostgresStore
    # --------------------------------------------------------

    async with AsyncPostgresStore.from_conn_string(
        DB_URI,
        pool_config=PoolConfig(
            min_size=1,
            max_size=20,
        ),
        index={
            "dims": 1024,
            "embed": get_vector,
            "fields": ["text"],
        },
    ) as store:

        # ----------------------------------------------------
        # 初始化数据库
        # ----------------------------------------------------

        print("\n正在初始化 AsyncPostgresStore...")

        await store.setup()

        print("✅ AsyncPostgresStore 初始化完成")


        # ----------------------------------------------------
        # 写入长期记忆
        # ----------------------------------------------------

        namespace = (
            "users",
            "user_123",
            "memories",
        )

        print("\n正在写入长期记忆...")

        await store.aput(
            namespace=namespace,
            key="pref_food",
            value={
                "text": (
                    "用户非常喜欢吃辣，"
                    "尤其是四川火锅和香辣蟹，"
                    "但不接受甜辣口。"
                )
            },
        )

        await store.aput(
            namespace=namespace,
            key="pref_work",
            value={
                "text": (
                    "用户是一名 Python 工程师，"
                    "喜欢使用 Docker 和 PostgreSQL。"
                )
            },
        )

        print("✅ 长期记忆写入完成")


        # ----------------------------------------------------
        # 语义搜索
        # ----------------------------------------------------

        print("\n--- 正在执行语义检索 ---")

        results = await store.asearch(
            namespace,
            query="用户在饮食上有什么特殊偏好吗？",
            limit=2,
        )

        for item in results:
            print(f"匹配到的 Key: {item.key}")
            print(f"记忆内容: {item.value}")
            print(f"相关度: {item.score}")
            print("---")


        # ====================================================
        # Graph Node
        # ====================================================

        async def chatbot_node(
            state: MessagesState,
            store: AsyncPostgresStore,
        ):

            last_msg = state["messages"][-1]

            user_input = (
                last_msg.content
                if isinstance(last_msg.content, str)
                else str(last_msg.content)
            )

            memories = await store.asearch(
                namespace,
                query=user_input,
                limit=2,
            )

            memory_context = "\n".join(
                m.value["text"]
                for m in memories
                if "text" in m.value
            )

            print("\n[节点内检索到的记忆上下文]:")
            print(memory_context)

            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": (
                            "已基于你的个人偏好处理完毕。\n\n"
                            f"相关长期记忆：\n"
                            f"{memory_context}"
                        ),
                    }
                ]
            }


        # ----------------------------------------------------
        # Graph
        # ----------------------------------------------------

        builder = StateGraph(MessagesState)

        builder.add_node(
            "chatbot",
            chatbot_node,
        )

        builder.add_edge(
            START,
            "chatbot",
        )

        builder.add_edge(
            "chatbot",
            END,
        )

        graph = builder.compile(
            store=store
        )


        # ----------------------------------------------------
        # Graph 测试
        # ----------------------------------------------------

        print("\n--- 正在运行 Graph ---")

        result = await graph.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        content="给我推荐点今晚想吃的美食"
                    )
                ]
            }
        )

        print("\n--- Graph 最终结果 ---")

        for message in result["messages"]:
            print(
                f"{message.type}: "
                f"{message.content}"
            )


if __name__ == "__main__":
    asyncio.run(main())