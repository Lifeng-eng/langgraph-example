"""
练习 1：用 Qwen3-Embedding 构建支持语义检索的 InMemoryStore

链路：
    Qwen3-Embedding  ->  InMemoryStore  ->  semantic search

核心思路：
    InMemoryStore 只有配置了 index 才支持向量检索。
    index 里的 embed 负责把文本转成向量，dims 是向量维度。
    这里我们直接把 dashscope 的 embedding 封装成一个函数传给 embed。
"""

import os
from typing import List

import dashscope
from dotenv import load_dotenv
from langgraph.store.memory import InMemoryStore

load_dotenv(override=True)
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# ---- 1. 配置 embedding 模型 ----
EMBEDDING_MODEL = "qwen3.7-text-embedding"  # 你已配置好的 Qwen3-Embedding 模型名
BATCH_SIZE = 10  # dashscope 单次请求对 input 数量有限制，分批调用


def embed_texts(texts: List[str]) -> List[List[float]]:
    """把一批文本转成向量（同步函数，供 InMemoryStore 调用）。

    dashscope 返回的 embeddings 顺序与 input 一致，直接按返回顺序取即可。
    """
    vectors: List[List[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = dashscope.TextEmbedding.call(model=EMBEDDING_MODEL, input=batch)

        if resp.status_code != 200:
            raise RuntimeError(f"Embedding 调用失败: {resp.status_code} {resp.message}")

        vectors.extend(e["embedding"] for e in resp.output["embeddings"])

    return vectors


def probe_dims() -> int:
    """先嵌入一句话，动态拿到真实向量维度，避免手写 dims 猜错。"""
    return len(embed_texts(["维度探测"])[0])


# ---- 2. 创建支持语义检索的 InMemoryStore ----
store = InMemoryStore(
    index={
        "dims": probe_dims(),
        "embed": embed_texts,  # 存和查都会走这个函数
        "fields": ["text"],  # 只对 value["text"] 字段做向量化
    }
)

# ---- 3. 写入几条记忆 ----
namespace = ("users", "user_001", "memories")

store.put(namespace, "tech_stack", {"text": "我是 Java 后端开发者"})
store.put(namespace, "habit", {"text": "我喜欢晚上学习"})
store.put(namespace, "food", {"text": "我喜欢吃面"})
store.put(namespace, "sport", {"text": "我周末喜欢打篮球"})


def main() -> None:
    # ---- 4. 语义检索 ----
    # 注意：查询词 "我平时用什么语言写代码" 和存储的原文没有一个字相同，
    # 但向量空间里语义接近，所以能召回到 tech_stack。
    query = "我平时用什么语言写代码"
    print(f"查询: {query}\n")

    results = store.search(namespace, query=query, limit=3)
    for rank, item in enumerate(results, start=1):
        print(f"{rank}. key={item.key:<10} score={item.score:.4f}  {item.value['text']}")

    print("\n--- 对照：关键词语义无关的查询 ---")
    results2 = store.search(namespace, query="吃东西的口味偏好", limit=3)
    for rank, item in enumerate(results2, start=1):
        print(f"{rank}. key={item.key:<10} score={item.score:.4f}  {item.value['text']}")


if __name__ == "__main__":
    main()
