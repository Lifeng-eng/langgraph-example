from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings

load_dotenv(override=True)

embeddings = DashScopeEmbeddings(
    model="qwen3.7-text-embedding-flash"
)

vec = embeddings.embed_query("测试一下")

print("类型:", type(vec))
print("维度:", len(vec))
print("前5个向量:", vec[:5])