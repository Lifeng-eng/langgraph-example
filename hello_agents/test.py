import time
from typing import List, Annotated, Literal
import operator
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

# 1. 定义更丰富的工单状态 Schema
class TicketState(BaseModel):
    ticket_id: str                      # 工单ID
    raw_user_input: str                 # 用户原始输入
    is_valid: bool = True               # 输入是否合法
    category: str = "未分类"             # 工单类别：技术支持 / 财务退款 / 垃圾信息
    priority: str = "普通"               # 优先级：高 / 中 / 低
    resolution: str = ""                # 最终处理意见
    cur_id: str = "init"                # 当前处理节点
    logs: Annotated[List[str], operator.add] = []  # 全局流水审计日志

# 2. 节点 1：输入校验与敏感词过滤（模拟数据清洗逻辑）
def input_validator_node(state: TicketState) -> dict:
    print(f"\n[Node 1: 校验节点] 正在处理工单 {state.ticket_id}...")
    time.sleep(0.5) # 模拟业务耗时
    
    text = state.raw_user_input
    sensitive_words = ["炸弹", "刷单", "赌博"]
    
    # 模拟校验逻辑
    if not text.strip():
        return {
            "is_valid": False,
            "resolution": "拒绝处理：用户输入内容为空",
            "cur_id": "validator",
            "logs": [f"[{time.strftime('%H:%M:%S')}] [Validator] 校验失败：内容为空"]
        }
        
    for word in sensitive_words:
        if word in text:
            return {
                "is_valid": False,
                "resolution": "拒绝处理：包含违规敏感词汇",
                "cur_id": "validator",
                "logs": [f"[{time.strftime('%H:%M:%S')}] [Validator] 拦截敏感词: {word}"]
            }
            
    return {
        "is_valid": True,
        "cur_id": "validator",
        "logs": [f"[{time.strftime('%H:%M:%S')}] [Validator] 文本校验通过"]
    }

# 3. 节点 2：意图分类与优先级打标（模拟分类逻辑 / 调用分类模型）
def intent_classifier_node(state: TicketState) -> dict:
    print(f"[Node 2: 分类节点] 正在分析文本意图...")
    text = state.raw_user_input
    
    # 模拟规则分流/模型推理
    if "退款" in text or "扣费" in text:
        cat = "财务退款"
        prio = "高"
    elif "无法登录" in text or "报错" in text or "卡顿" in text:
        cat = "技术支持"
        prio = "中"
    else:
        cat = "综合咨询"
        prio = "低"
        
    return {
        "category": cat,
        "priority": prio,
        "cur_id": "classifier",
        "logs": [f"[{time.strftime('%H:%M:%S')}] [Classifier] 识别分类为: [{cat}], 优先级: [{prio}]"]
    }

# 4. 节点 3：自动生成解决方案（模拟业务逻辑/调用大模型生成回复）
def auto_resolver_node(state: TicketState) -> dict:
    print(f"[Node 3: 解决节点] 正在根据分类 [{state.category}] 生成解决方案...")
    
    # 模拟针对不同分类的自动处理流程
    if state.category == "财务退款":
        solution = "已为您触发系统预审，退款申请已提交至财务后台，预计1个工作日内到账。"
    elif state.category == "技术支持":
        solution = "建议您先尝试清除客户端缓存并重启应用。若仍无法解决，已自动为您转接二线技术专家。"
    else:
        solution = "感谢您的反馈，常见问题可参考帮助中心文档：https://docs.example.com"
        
    return {
        "resolution": solution,
        "cur_id": "resolver",
        "logs": [f"[{time.strftime('%H:%M:%S')}] [Resolver] 成功自动生成解决方案"]
    }

# 5. 条件路由函数：根据校验结果决定是否直接终止流程
def route_after_validation(state: TicketState) -> Literal["classifier", "__end__"]:
    if not state.is_valid:
        print("--> 检测到无效或非法工单，流转直接终止 (END)")
        return END
    return "classifier"

# 6. 构建图结构
builder = StateGraph(TicketState)

builder.add_node("validator", input_validator_node)
builder.add_node("classifier", intent_classifier_node)
builder.add_node("resolver", auto_resolver_node)

# 设置流程边
builder.add_edge(START, "validator")

# 条件边：Validator 处理完后，根据校验结果判断走 Classifier 还是直接 END
builder.add_conditional_edges(
    "validator",
    route_after_validation,
    {
        "classifier": "classifier",
        END: END
    }
)

builder.add_edge("classifier", "resolver")
builder.add_edge("resolver", END)

app = builder.compile()

# ================= 运行测试 =================
if __name__ == "__main__":
    # 运行用例 1：正常的技术支持工单
    print("======== 测试 1：正常工单处理 ========")
    input_1 = {
        "ticket_id": "TK-1001",
        "raw_user_input": "我的App今天一直卡顿，报错500无法登录！"
    }
    result_1 = app.invoke(input_1)
    print("\n【最终工单处理单】:")
    print(f"工单ID: {result_1['ticket_id']}")
    print(f"分类/优先级: {result_1['category']} / {result_1['priority']}")
    print(f"处理结果: {result_1['resolution']}")
    print("审计日志历史:")
    for log in result_1["logs"]:
        print(" ", log)

    print("\n" + "="*40 + "\n")

    # 运行用例 2：包含非法违规词的工单（测试条件分支拦截）
    print("======== 测试 2：违规工单拦截 ========")
    input_2 = {
        "ticket_id": "TK-1002",
        "raw_user_input": "加我QQ拉你进群一起刷单赚钱"
    }
    result_2 = app.invoke(input_2)
    print("\n【最终工单处理单】:")
    print(f"处理结果: {result_2['resolution']}")
    print("审计日志历史:")
    for log in result_2["logs"]:
        print(" ", log)
from IPython.display import display,Image
display(Image(app.get_graph().draw_mermaid_png()))
display(builder)