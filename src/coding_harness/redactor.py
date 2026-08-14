"""密钥擦除器：从任意文本中擦除真实形状的 sk-ant- API 密钥。

作为安全边界贯穿全 harness：每个 ToolResult / Event payload 在落日志前
经 redact() 处理，确保密钥绝不进入事件日志或工具输出。
"""
import re

SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]+"),
]
_REPLACEMENT = "sk-ant-***REDACTED***"

def redact(text: str) -> str:
    """将文本中所有匹配 SECRET_PATTERNS 的密钥替换为脱敏占位符。"""
    out = text
    for pat in SECRET_PATTERNS:
        out = pat.sub(_REPLACEMENT, out)
    return out
