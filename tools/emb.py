import os
from typing import List
from dotenv import load_dotenv
import dashscope

from langchain_core.embeddings import Embeddings
from langgraph.store.memory import InMemoryStore

load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# --- Step 1: 封装 Qwen3-Embedding 为 LangChain 标准 Embeddings 类 ---
class QwenEmbeddings(Embeddings):
    def __init__(self, model_name: str = "qwen3.7-text-embedding"):
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        resp = dashscope.TextEmbedding.call(
            model=self.model_name,
            input=texts
        )
        if resp.status_code == 200:
            embeddings = resp.output['embeddings']
            # 保证按原始输入顺序提取向量
            return [item['embedding'] for item in sorted(embeddings, key=lambda x: x['text_index'])]
        else:
            raise Exception(f"DashScope Embedding API 错误: {resp.code} - {resp.message}")

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


# --- Step 2: 初始化 Qwen Embedding 实例 ---
embedding_model = QwenEmbeddings(model_name="qwen3.7-text-embedding")


# --- Step 3: 配置并创建 LangGraph 的 InMemoryStore ---
# 通过 index 参数指定使用的 embedding 模型和要对哪些字段建立向量索引
store = InMemoryStore(
    index={
        "embed": embedding_model, # 指定向量模型
        "dims": 1024,             # 向量维度 (根据 Qwen embedding 模型实际输出调整)
        "fields": ["text"],       # 指定对存储对象中的哪些 key/fields 生成向量
    }
)


# --- Step 4: 写入数据到 LangGraph Store ---
# LangGraph Store 的数据按 (namespace, key, value) 三层结构组织
namespace = ("users", "user_123", "memories")

store.put(
    namespace=namespace,
    key="mem_1",
    value={"text": "阿里云 DashScope 提供高性能的大模型 API 服务。", "category": "cloud"}
)

store.put(
    namespace=namespace,
    key="mem_2",
    value={"text": "苹果是一种富含维生素和膳食纤维的常见水果。", "category": "fruit"}
)

store.put(
    namespace=namespace,
    key="mem_3",
    value={"text": "通义千问是阿里云自主研发的超大规模语言模型。", "category": "ai"}
)

store.put(
    namespace=namespace,
    key="mem_4",
    value={"text": "向量数据库主要用于存储和快速检索高维向量数据。", "category": "database"}
)


# --- Step 5: 执行 Semantic Search (语义搜索) ---
query_text = "阿里有哪些人工智能产品？"

# 使用 store.search() 进行语义检索
results = store.search(
    namespace,          # 第一个参数是位置参数，不能写成 namespace_prefix=
    query=query_text,
    limit=2             # 返回 Top 2
)


# --- Step 6: 打印检索结果 ---
print(f"查询语句: {query_text}\n")
print("=== 检索到的语义相关 Memory Item ===")
for i, item in enumerate(results, 1):
    print(f"{i}. Key: {item.key}")
    print(f"   Value: {item.value}")
    print(f"   Score (相似度得分): {item.score}\n")
