"""
测试文件解析中的LLM接口调用
"""

import pytest
from unittest.mock import patch, MagicMock

from llm_client import call_llm, extract_json_from_text
from audit_prompt import build_file_audit_prompt


class TestExtractJsonFromText:
    """测试 JSON 提取函数"""

    def test_extract_plain_json(self):
        text = '{"passed": true, "reason": "", "details": "符合要求"}'
        result = extract_json_from_text(text)
        assert result["passed"] is True

    def test_extract_json_from_markdown_block(self):
        text = '''这是审核结果：
```json
{"passed": false, "reason": "缺少必要字段", "details": ""}
```
'''
        result = extract_json_from_text(text)
        assert result["passed"] is False
        assert result["reason"] == "缺少必要字段"

    def test_extract_json_with_surrounding_text(self):
        text = '审核完成，结果如下：{"passed": true, "reason": ""} 请查收'
        result = extract_json_from_text(text)
        assert result["passed"] is True

    def test_no_json_raises_error(self):
        with pytest.raises(ValueError, match="未找到 JSON"):
            extract_json_from_text("这里没有JSON内容")


class TestBuildFileAuditPrompt:
    """测试审核提示词构建"""

    def test_build_prompt_basic(self):
        messages = build_file_audit_prompt(
            review_background="测试背景",
            parse_rules="检查文档格式",
            file_name="test.txt",
            file_content="测试内容",
        )
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "测试背景" in messages[1]["content"]
        assert "test.txt" in messages[1]["content"]

    def test_build_prompt_with_background_files(self):
        bg_files = [
            {"fileName": "规范.pdf", "textContent": "这是规范内容"},
            {"fileName": "标准.docx", "textContent": "这是标准内容"},
        ]
        messages = build_file_audit_prompt(
            background_files=bg_files,
            file_content="待审核内容",
        )
        assert "规范.pdf" in messages[1]["content"]
        assert "标准.docx" in messages[1]["content"]


class TestCallLlm:
    """测试 LLM 调用（使用 Mock）"""

    @patch("llm_client.httpx.Client")
    def test_call_llm_success(self, mock_client_class):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '{"passed": true, "reason": ""}'}}
            ]
        }
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = call_llm([{"role": "user", "content": "测试"}])
        assert "passed" in result

    @patch("llm_client.httpx.Client")
    def test_call_llm_empty_response_raises(self, mock_client_class):
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        with pytest.raises(ValueError, match="返回内容为空"):
            call_llm([{"role": "user", "content": "测试"}])


class TestLlmIntegration:
    """测试 LLM 集成（端到端 Mock 测试）"""

    @patch("llm_client.httpx.Client")
    def test_full_audit_flow(self, mock_client_class):
        """模拟完整的文件审核 LLM 调用流程"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '{"passed": true, "reason": "", "details": "符合规范"}'}}
            ]
        }
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        messages = build_file_audit_prompt(
            review_background="质量审核背景",
            parse_rules="检查文档是否符合GB标准",
            file_name="report.docx",
            file_content="这是一份质量报告内容...",
        )

        llm_response = call_llm(messages)
        result = extract_json_from_text(llm_response)

        assert result["passed"] is True
        assert result["details"] == "符合规范"

    @patch("llm_client.httpx.Client")
    def test_audit_failed_flow(self, mock_client_class):
        """模拟审核不通过的场景"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '{"passed": false, "reason": "缺少必填字段", "details": ""}'}}
            ]
        }
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        messages = build_file_audit_prompt(
            review_background="测试",
            parse_rules="检查完整性",
            file_content="不完整的内容",
        )

        llm_response = call_llm(messages)
        result = extract_json_from_text(llm_response)

        assert result["passed"] is False
        assert "缺少必填字段" in result["reason"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
