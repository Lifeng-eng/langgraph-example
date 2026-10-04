# -*- coding: utf-8 -*-
"""
词法分析程序 - 扫描器的设计
"""

# 关键字与符号定义表 (下标+1 对应相应的编码 code)
KEYWORDS = [
    "program", "begin", "end", "var", "while", "do",
    "repeat", "until", "for", "to", "if", "then", "else",
    ";", ":", "(", ")", ":=", "+", "-", "*", "/",
    ">", ">=", "==", "<", "<="
]

# 状态转换矩阵 aut[10][7]
# 列索引含义: 0:d(数字), 1:.(小数点), 2:e, 3:+/-, 4:l(字母), 5:b(界符), 6:-1(其他)
AUT = [
    [2, 0, 0, 0, 8, 9, 15],  # State 1 (索引 0)
    [2, 3, 5, 11, 0, 0, 11], # State 2 (索引 1)
    [4, 0, 0, 0, 0, 0, 0],   # State 3 (索引 2)
    [4, 0, 5, 11, 0, 0, 11], # State 4 (索引 3)
    [7, 0, 0, 6, 0, 0, 0],   # State 5 (索引 4)
    [7, 0, 0, 0, 0, 0, 0],   # State 6 (索引 5)
    [7, 0, 0, 11, 0, 0, 11], # State 7 (索引 6)
    [8, 0, 0, 0, 8, 0, 12],  # State 8 (索引 7)
    [0, 0, 0, 0, 0, 10, 14], # State 9 (索引 8)
    [0, 0, 0, 0, 0, 0, 13]   # State 10 (索引 9)
]

class Token:
    def __init__(self, code, value):
        self.code = code      # 单词种别码/类型
        self.value = value    # 符号表索引、常数表索引或对应值

    def __repr__(self):
        return f"<Token code={self.code}, value={self.value}>"

class LexicalAnalyzer:
    def __init__(self, source_code):
        self.w = source_code
        self.i = 0
        self.ID_table = []   # 标识符表
        self.C_table = []    # 常数表
        self.tokens = []     # 存放识别出的 Token 序列

    def get_char_type(self, ch):
        """判断字符类型，返回状态矩阵对应的列索引"""
        if ch.isdigit():
            return 0  # d (数字)
        elif ch == '.':
            return 1  # . (小数点)
        elif ch in ['e', 'E']:
            return 2  # e
        elif ch in ['+', '-']:
            return 3  # +/-
        elif ch.isalpha():
            return 4  # l (字母)
        elif ch in [';', ':', '(', ')', '=', '>', '<', '*', '/']:
            return 5  # b (界符/运算符)
        else:
            return 6  # -1 (其他字符)

    def analyze(self):
        n_len = len(self.w)
        while self.i < n_len:
            # 跳过空白字符
            if self.w[self.i].isspace():
                self.i += 1
                continue

            state = 1
            token_str = ""

            while state not in [11, 12, 13, 14, 15]:
                if self.i >= n_len:
                    # 到达末尾，强制触发终态
                    if state in [2, 4, 7]:
                        state = 11
                    elif state == 8:
                        state = 12
                    elif state == 9:
                        state = 14
                    elif state == 10:
                        state = 13
                    else:
                        state = 15
                    break

                ch = self.w[self.i]
                col = self.get_char_type(ch)

                # 在状态2或4遇到 'e'，作为指数标志；但在状态8（标识符中）'e' 只是常规字母
                if state == 8 and col == 2:
                    col = 4

                next_state = AUT[state - 1][col]

                if next_state == 0:
                    # 无有效转换，转移至终态
                    if state in [2, 4, 7]:
                        next_state = 11
                    elif state == 8:
                        next_state = 12
                    elif state == 9:
                        next_state = 14
                    else:
                        next_state = 15

                # 记录字符并移动指针（终态前）
                if next_state not in [11, 12, 13, 14, 15]:
                    token_str += ch
                    self.i += 1

                state = next_state

            # 根据到达的终态进行语义处理与 Token 生成
            if state == 11:  # 常数识别完成
                try:
                    num_val = float(token_str)
                except ValueError:
                    num_val = int(token_str)
                if num_val not in self.C_table:
                    self.C_table.append(num_val)
                c_idx = self.C_table.index(num_val)
                self.tokens.append(Token(code=100, value=c_idx)) # 100 代表常数类别

            elif state == 12:  # 标识符或关键字识别完成
                if token_str in KEYWORDS:
                    code = KEYWORDS.index(token_str) + 1
                    self.tokens.append(Token(code=code, value=token_str))
                else:
                    if token_str not in self.ID_table:
                        self.ID_table.append(token_str)
                    id_idx = self.ID_table.index(token_str)
                    self.tokens.append(Token(code=200, value=id_idx)) # 200 代表标识符类别

            elif state in [13, 14]:  # 界符/双字符界符识别完成
                if token_str in KEYWORDS:
                    code = KEYWORDS.index(token_str) + 1
                    self.tokens.append(Token(code=code, value=token_str))
                else:
                    # 单字符界符未完全匹配时的兜底
                    self.tokens.append(Token(code=999, value=token_str))

            elif state == 15:  # 未知/未识别字符
                ch = self.w[self.i]
                self.tokens.append(Token(code=-1, value=ch))
                self.i += 1

    def print_results(self):
        print("=== Token 序列 ===")
        for tok in self.tokens:
            print(tok)
        print("\n=== 符号表 (ID) ===")
        for idx, item in enumerate(self.ID_table):
            print(f"[{idx}]: {item}")
        print("\n=== 常数表 (C) ===")
        for idx, item in enumerate(self.C_table):
            print(f"[{idx}]: {item}")

# ----------------- 测试运行 -----------------
if __name__ == "__main__":
    test_case_1 = """program test;
var b:integer;
b:=45.6e+7;
while b < 1000 do
begin
    repeat
        b:=b+10;
    until b = 999;
end;"""

    test_case_2 = "if x<=123.4e-5 then y:=x+2;"

    print("******************** 测试用例 1 ********************")
    lexer1 = LexicalAnalyzer(test_case_1)
    lexer1.analyze()
    lexer1.print_results()

    print("\n******************** 测试用例 2 ********************")
    lexer2 = LexicalAnalyzer(test_case_2)
    lexer2.analyze()
    lexer2.print_results()
