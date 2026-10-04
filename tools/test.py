from dotenv import load_dotenv
import os
import dashscope

# 加载 .env 文件
load_dotenv()

# 从环境变量里读取你自定义的名字，然后赋值给 dashscope
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# 后面正常调用即可
input_texts = ["你好", "通用多模态表征模型示例"]

resp = dashscope.TextEmbedding.call(
    model="qwen3.7-text-embedding-flash",
    input=input_texts
)
for item in resp["output"]["embeddings"]:
    print(item["embedding"][:3])
# print(resp)
