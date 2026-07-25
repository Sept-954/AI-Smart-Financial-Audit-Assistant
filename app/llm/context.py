"""长对话上下文管理——参考 Dexter compact.ts 的自动摘要策略。"""

from collections import deque


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数（中文 ~1.5 token/字，英文 ~0.25 token/字符）。"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars * 1.5 + other_chars * 0.25)


class ContextManager:
    """管理长对话上下文窗口。
    
    参考 Dexter compact.ts 的固定窗口 + 自动摘要策略。
    PRD 3.3：固定窗口（最近 3000 token）+ 超过后自动摘要历史。
    """
    
    def __init__(self, max_tokens: int = 3000):
        self.history: deque[dict] = deque()
        self.max_tokens = max_tokens
        self.summary: str = ""
    
    def add_turn(self, question: str, answer: str) -> None:
        """添加一轮问答。如果超 token 预算，压缩最早的内容为摘要。"""
        self.history.append({"q": question, "a": answer})
        if self._total_tokens() > self.max_tokens:
            self._compact()
    
    def get_history_summary(self) -> str:
        """获取历史摘要 + 最近对话。"""
        parts = []
        if self.summary:
            parts.append(f"[历史摘要] {self.summary}")
        for turn in self.history:
            parts.append(f"问: {turn['q']}\n答: {turn['a']}")
        return "\n\n".join(parts)
    
    def _total_tokens(self) -> int:
        text = self.summary + " ".join(
            f"{t['q']} {t['a']}" for t in self.history
        )
        return estimate_tokens(text)
    
    def _compact(self) -> None:
        """把最早的一半对话压缩为摘要。"""
        n = len(self.history)
        if n <= 1:
            return
        # 取最早的一半做压缩
        half = n // 2
        old_turns = []
        for _ in range(half):
            old_turns.append(self.history.popleft())
        
        # 构建压缩文本（实际项目中应由 LLM fast model 执行）
        old_text = "; ".join(f"Q:{t['q']} A:{t['a']}" for t in old_turns)
        if self.summary:
            self.summary = f"{self.summary}; {old_text[:200]}"
        else:
            self.summary = old_text[:200]
    
    def clear(self) -> None:
        self.history.clear()
        self.summary = ""
