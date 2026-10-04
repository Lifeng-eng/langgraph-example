import time
from pydantic import BaseModel

class SearchProductArgs(BaseModel):
    keyword: str
    limit: int
search_args = SearchProductArgs(
    keyword="Python 教程",
    limit=3
)
print(search_args)
