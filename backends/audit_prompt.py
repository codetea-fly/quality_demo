"""
审核步骤 - 提示词生成
根据审核背景、背景技术文件、解析规则，生成调用大模型进行文件审核的提示词
"""

from typing import Any


# 统一审核步骤结果的 JSON schema 说明（用于引导大模型输出格式）
AUDIT_RESULT_SCHEMA = """
请以严格的 JSON 格式返回审核结果，且只返回 JSON，不要包含其他说明文字。
格式如下：
{
  "passed": true 或 false,
  "reason": "不通过原因，仅当 passed 为 false 时必填；通过时可为空字符串",
  "details": "可选，审核详情或改进建议"
}
"""


def build_file_audit_prompt(
    *,
    review_background: str = "",
    background_files: list[dict[str, Any]] | None = None,
    parse_rules: str = "",
    file_name: str = "",
    file_content: str = "",
) -> list[dict[str, str]]:
    """
    构建文件审核的提示词（系统提示 + 用户消息）。

    Args:
        review_background: 审核背景描述
        background_files: 背景技术文件列表 [{"fileName": "xxx", "textContent": "..."}]
        parse_rules: 审核步骤中配置的解析规则
        file_name: 待审核文件名
        file_content: 待审核文件内容

    Returns:
        messages 列表，可直接传入 call_llm
    """
    background_files = background_files or []

    # 背景技术文件内容拼接
    bg_sections = []
    for f in background_files:
        name = f.get("fileName", f.get("name", "未知文件"))
        content = f.get("textContent", f.get("content", ""))
        if content:
            bg_sections.append(f"### {name}\n```\n{content[:15000]}\n```")  # 限制长度

    bg_text = "\n\n".join(bg_sections) if bg_sections else "（无背景技术文件）"
    rules_text = parse_rules.strip() or "无具体解析规则，请基于通用质量审核标准进行评估。"
    background_text = review_background.strip() or "无特定审核背景。"

    system_prompt = f"""你是一个专业的质量审核助手。你的任务是根据审核背景、参考技术文件和解析规则，对提交的待审核文件进行合规性审核。

请严格按照以下规则进行评估：
1. 结合审核背景理解审核目标；
2. 参考背景技术文件中的要求、标准或规范；
3. 依据解析规则逐项检查待审核文件；
4. 给出明确的审核结论（通过/不通过）及理由。

{AUDIT_RESULT_SCHEMA}
"""

    user_content = f"""## 审核背景
{background_text}

## 参考背景技术文件
{bg_text}

## 解析规则（本步骤的审核依据）
{rules_text}

## 待审核文件
- 文件名：{file_name or "未命名"}
- 内容：
```
{file_content[:30000] if file_content else "（文件内容为空）"}
```

请根据上述信息进行审核，并仅返回符合格式要求的 JSON 审核结果。"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
