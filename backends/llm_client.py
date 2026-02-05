"""
LLM 客户端 - 调用大模型 API
与前端 ChatInterface 一致，使用 FastGPT 风格接口（appId、Authorization 可配置）

配置见 llm_config.py，环境变量可覆盖：
  LLM_API_BASE    - API 基础 URL
  LLM_APP_ID      - FastGPT appId
  LLM_AUTH_TOKEN  - Authorization Bearer Token
"""

import json
import re
import uuid
from typing import Optional

import httpx

from llm_config import AUDIT_APP_ID, AUDIT_AUTH_TOKEN, LLM_API_BASE


def call_llm(
    messages: list[dict],
    *,
    api_base: Optional[str] = None,
    app_id: Optional[str] = None,
    auth_token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> str:
    """
    调用大模型 API（FastGPT 风格，与 ChatInterface 一致），返回完整回复文本。

    Args:
        messages: 消息列表 [{"role": "user"|"system"|"assistant", "content": "..."}]
        api_base: API 基础 URL，默认 LLM_API_BASE
        app_id: FastGPT appId，默认 LLM_APP_ID，其他接口可传不同值
        auth_token: Authorization Bearer Token，默认 LLM_AUTH_TOKEN
        chat_id: 会话 ID，不传则自动生成

    Returns:
        模型回复的文本内容

    Raises:
        ValueError: 当 API 调用失败时
    """
    base = api_base or LLM_API_BASE
    aid = app_id or AUDIT_APP_ID
    token = auth_token or AUDIT_AUTH_TOKEN
    cid = chat_id or f"audit-{uuid.uuid4().hex[:16]}"

    url = f"{base.rstrip('/')}/v2/chat/completions"

    headers = {
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "appId": aid,
        "chatId": cid,
        "stream": False,
        "detail": False,
        "messages": messages,
    }

    try:
        with httpx.Client(timeout=120.0, proxy=None, trust_env=False) as client:
            resp = client.post(url, json=payload, headers=headers)
            print(f"[call_llm] status: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        raise ValueError(f"LLM API 请求失败: {e.response.status_code} - {e.response.text}") from e
    except Exception as e:
        raise ValueError(f"LLM API 调用异常: {e}") from e

    choice = data.get("choices")
    if not choice:
        raise ValueError("LLM 返回格式异常: 无 choices")

    content = choice[0].get("message", {}).get("content", "")
    if not content:
        raise ValueError("LLM 返回内容为空")

    return content.strip()


def extract_json_from_text(text: str) -> dict:
    """
    从模型回复中提取 JSON 对象。
    支持回复被 markdown 代码块包裹的情况。
    """
    # 尝试直接解析
    text = text.strip()

    # 去除 ```json ... ``` 包裹
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if json_match:
        text = json_match.group(1).strip()

    # 查找 { ... } 范围
    start = text.find("{")
    if start == -1:
        raise ValueError("回复中未找到 JSON 对象")

    depth = 0
    end = -1
    for i, c in enumerate(text[start:], start):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    if end == -1:
        raise ValueError("JSON 对象括号不匹配")

    json_str = text[start : end + 1]
    return json.loads(json_str)
