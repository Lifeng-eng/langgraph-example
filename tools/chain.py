import traceback
from typing import Any, Dict, Literal


# 1. 定义函数
def calculator(a: float, b: float, Operator: Literal["+", "-", "*", "/"]) -> float:
    if Operator == "+":
        return a + b
    elif Operator == "-":
        return a - b
    elif Operator == "*":
        return a * b
    elif Operator == "/":
        if b == 0:
            raise ZeroDivisionError("Division by zero is not allowed.")
        return a / b
    else:
        raise ValueError(
            f"Invalid operator '{Operator}'. Must be one of ['+', '-', '*', '/']."
        )


def get_weather(city: str) -> str:
    return f"{city}:晴，25度"


def search_user(user_id: str) -> str:
    return f"用户 {user_id}：张三"


# 2. Tool Registry
tools = {
    "calculator": calculator,
    "get_weather": get_weather,
    "search_user": search_user,
}


# 3. 增强版 Tool 执行器
def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    # 场景 1: tool_name 不存在
    if tool_name not in tools:
        available_tools = ", ".join(tools.keys())
        return f"[Tool Error] Tool '{tool_name}' is not found. Available tools are: [{available_tools}]."

    target_func = tools[tool_name]

    try:
        # 场景 2 & 场景 3: 尝试调用函数并捕捉参数匹配错误或运行中异常
        result = target_func(**arguments)
        return str(result)

    except TypeError as e:
        # 场景 2: 参数缺少/多余/不匹配 (TypeError)
        return f"[Tool Parameter Error] Invalid arguments passed to '{tool_name}': {e}. Provided arguments: {arguments}"

    except Exception as e:
        # 场景 3: 函数内部执行异常 (ZeroDivisionError, ValueError, Network Error 等)
        return (
            f"[Tool Execution Error] Exception occurred while executing '{tool_name}': {type(e).__name__}: {e}"
        )


# ================= 测试防护逻辑 =================
if __name__ == "__main__":
    print("--- 1. 测试工具不存在 ---")
    print(execute_tool("search_google", {"query": "Python"}))
    # 输出: [Tool Error] Tool 'search_google' is not found. Available tools are: [calculator, get_weather, search_user].

    print("\n--- 2. 测试参数不正确 (少了必需参数/多传参数) ---")
    print(execute_tool("calculator", {"a": 10}))
    # 输出: [Tool Parameter Error] Invalid arguments passed to 'calculator': calculator() missing 2 required positional arguments: 'b' and 'Operator'...

    print("\n--- 3. 测试 Tool 内部执行引发异常 (除以 0) ---")
    print(execute_tool("calculator", {"a": 10, "b": 0, "Operator": "/"}))
    # 输出: [Tool Execution Error] Exception occurred while executing 'calculator': ZeroDivisionError: Division by zero is not allowed.

    print("\n--- 4. 测试合法调用 ---")
    print(execute_tool("calculator", {"a": 10, "b": 2, "Operator": "/"}))
    # 输出: 5.0
