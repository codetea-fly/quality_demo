"""
测试真实 LLM 接口调用（文件解析审核）
"""

from llm_client import call_llm, extract_json_from_text
from audit_prompt import build_file_audit_prompt


def test_real_llm_call():
    """测试真实 LLM 接口调用"""
    
    # 构建审核 prompt
    messages = build_file_audit_prompt(
        review_background="质量管理体系审核",
        parse_rules="检查文档是否包含必要的质量控制要素：目的、范围、职责、流程",
        file_name="质量管理手册.docx",
        file_content="""
        质量管理手册
        
        
        2. 范围
        适用于公司所有产品的生产、检验和交付过程。
        
        3. 职责
        - 质量部：负责质量体系的建立和维护
        - 生产部：负责按照质量要求进行生产
        - 检验员：负责产品检验和记录
        
        4. 流程
        4.1 来料检验
        4.2 过程控制
        4.3 成品检验
        4.4 不合格品处理
        """,
    )

    print("=" * 50)
    print("发送 Prompt 到 LLM...")
    print("=" * 50)
    
    # 调用 LLM
    response = call_llm(messages)
    print(f"\nLLM 原始响应:\n{response}")
    
    # 解析 JSON 结果
    result = extract_json_from_text(response)
    print(f"\n解析后的审核结果:")
    print(f"  通过: {result.get('passed')}")
    print(f"  原因: {result.get('reason', '')}")
    print(f"  详情: {result.get('details', '')}")
    
    return result


if __name__ == "__main__":
    test_real_llm_call()
