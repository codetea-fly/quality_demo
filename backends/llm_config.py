"""
LLM 调用配置 - appId、Authorization 等预留，各接口可覆盖不同值
与前端 ChatInterface 保持一致，便于统一维护
"""

import os

# 基础 API 地址（FastGPT 等服务）
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://192.168.45.105:3000/api")

# 审核步骤-文件解析 等通用审核接口
AUDIT_APP_ID = os.getenv("LLM_APP_ID", "6983f33f9dda4ab3681ee1dc")
AUDIT_AUTH_TOKEN = os.getenv("LLM_AUTH_TOKEN", "fastgpt-j2JZgSp22RXUswC8SudmQGp8IYEhdm45gkr9zXL7S2KBoK0qrxL1dpVR")

# 聊天等其它接口可在此扩展，例如：
# CHAT_APP_ID = os.getenv("LLM_CHAT_APP_ID", "...")
# CHAT_AUTH_TOKEN = os.getenv("LLM_CHAT_AUTH_TOKEN", "...")
