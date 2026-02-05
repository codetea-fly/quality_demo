import json
import time
from typing import Optional, Any

from pydantic import BaseModel, Field
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from prompt_generate import generate_prompt_from_json
from file_parser import parse_file

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 审核步骤 - 文件解析 API 模型 ====================

class FileInfo(BaseModel):
    """文件信息"""
    id: str
    name: str
    type: str
    size: int
    url: Optional[str] = None


class PageRange(BaseModel):
    """页码范围"""
    start: int
    end: int


class ParseOptions(BaseModel):
    """解析选项"""
    format: Optional[str] = None  # pdf | docx | xlsx | csv | txt | json | xml
    extractText: Optional[bool] = None
    extractTables: Optional[bool] = None
    extractImages: Optional[bool] = None
    enableOcr: Optional[bool] = None
    pageRange: Optional[PageRange] = None


class BackgroundFileItem(BaseModel):
    """背景技术文件"""
    fileName: Optional[str] = Field(None, description="文件名")
    name: Optional[str] = None  # 兼容前端
    textContent: Optional[str] = Field(None, description="文件文本内容")
    content: Optional[str] = None  # 兼容


class CheckConfig(BaseModel):
    """审核步骤配置（文件解析）"""
    parseRules: Optional[str] = Field(None, description="解析规则")
    fileTypes: Optional[list[str]] = None


class FileParseRequest(BaseModel):
    """文件解析请求"""
    stepType: str = "file_parse"
    stepId: str
    workflowId: str
    sessionId: str
    userInput: Optional[Any] = None
    context: Optional[dict[str, Any]] = None
    file: Optional[FileInfo] = None
    parseOptions: Optional[ParseOptions] = None
    # 客户端可传入已提取的文本内容，后端直接构建返回
    textContent: Optional[str] = Field(None, description="待审核文件的文本内容")
    # 审核背景与参考文件（用于大模型审核）
    reviewBackground: Optional[str] = Field(None, description="审核背景")
    backgroundFiles: Optional[list[BackgroundFileItem]] = Field(None, description="背景技术文件列表")
    checkConfig: Optional[CheckConfig] = Field(None, description="审核步骤配置，含解析规则")


# ==================== 审核步骤 - 问答交互 API 模型 ====================

class QuestionConfig(BaseModel):
    question: Optional[str] = None
    expectedAnswer: Optional[str] = None
    useAiValidation: Optional[bool] = None
    aiValidationPrompt: Optional[str] = None


class QAInteractionRequest(BaseModel):
    """问答交互请求"""
    stepType: str = "qa_interaction"
    stepId: str
    workflowId: str
    sessionId: str
    userInput: Optional[Any] = None
    context: Optional[dict[str, Any]] = None
    answer: Optional[str] = None
    questionConfig: Optional[QuestionConfig] = None


# ==================== 审核步骤 - 单选 API 模型 ====================

class OptionItem(BaseModel):
    label: str
    value: str
    isCorrect: Optional[bool] = None


class OptionsConfig(BaseModel):
    options: list[OptionItem] = []
    shuffle: Optional[bool] = None


class SingleSelectRequest(BaseModel):
    """单选请求"""
    stepType: str = "single_select"
    stepId: str
    workflowId: str
    sessionId: str
    userInput: Optional[Any] = None
    context: Optional[dict[str, Any]] = None
    selectedValue: Optional[str] = None
    optionsConfig: Optional[OptionsConfig] = None


# ==================== 审核步骤 - 多选 API 模型 ====================

class MultiSelectOptionsConfig(BaseModel):
    options: list[OptionItem] = []
    minSelect: Optional[int] = None
    maxSelect: Optional[int] = None
    shuffle: Optional[bool] = None


class MultiSelectRequest(BaseModel):
    """多选请求"""
    stepType: str = "multi_select"
    stepId: str
    workflowId: str
    sessionId: str
    userInput: Optional[Any] = None
    context: Optional[dict[str, Any]] = None
    selectedValues: Optional[list[str]] = None
    optionsConfig: Optional[MultiSelectOptionsConfig] = None


# ==================== 审核步骤 - 脚本检查 API 模型 ====================

class ScriptContent(BaseModel):
    content: str
    language: Optional[str] = None  # javascript | python | sql


class ExecutionParams(BaseModel):
    timeout: Optional[int] = None
    memoryLimit: Optional[int] = None
    env: Optional[dict[str, str]] = None
    inputData: Optional[Any] = None


class ScriptCheckRequest(BaseModel):
    """脚本检查请求"""
    stepType: str = "script_check"
    stepId: str
    workflowId: str
    sessionId: str
    userInput: Optional[Any] = None
    context: Optional[dict[str, Any]] = None
    script: Optional[ScriptContent] = None
    executionParams: Optional[ExecutionParams] = None


# ==================== 审核步骤 - 子流程 API 模型 ====================

class ExecutionOptions(BaseModel):
    async_: Optional[bool] = Field(default=None, validation_alias="async")
    timeout: Optional[int] = None
    continueOnFailure: Optional[bool] = None


class SubWorkflowRequest(BaseModel):
    """子流程请求"""
    stepType: str = "sub_workflow"
    stepId: str
    workflowId: str
    sessionId: str
    userInput: Optional[Any] = None
    context: Optional[dict[str, Any]] = None
    subWorkflowId: str
    executionOptions: Optional[ExecutionOptions] = None


class Query(BaseModel):
    query: str
    background: str
    structure: str
    replace: str


@app.post("/prompt/generate")
def generate_prompt(query:Query):
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\knowledge.json','r',encoding='utf-8') as file:
        sample_json = json.load(file)
    prompt = generate_prompt_from_json(sample_json, query.query, query.background, query.structure, query.replace)
    return {"prompt": prompt}

@app.post("/knowledge/generate")
def generate_knowledge(query:Query):
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\knowledge.json','w',encoding='utf-8') as file:
        file.write(query.query)
    return {"result":"OK"}

@app.get("/knowledge/get")
def get_knowledge():
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\knowledge.json','r',encoding='utf-8') as file:
        sample_json = json.load(file)
        print(sample_json)
    return{"knowledge":sample_json}

@app.get("/template/get")
def get_template():
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\template.json','r',encoding='utf-8') as file:
        sample_json = json.load(file)
        return {
            "background":sample_json.get("background"),
            "structure":sample_json.get("structure"),
            "replace":sample_json.get("replace")
        }

@app.post("/template/generate")
def generate_template(query:Query):
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\template.json','w',encoding='utf-8') as file:
        content = json.dumps({"background":query.background, "structure":query.structure,"replace":query.replace})
        file.write(content)
    return {"result":"OK"}


# ==================== 审核步骤 - 文件解析 API ====================

def _run_file_audit_with_llm(request: FileParseRequest, text_content: str) -> dict | None:
    """
    使用大模型执行文件审核，返回统一审核结果。
    若未配置 LLM 或调用失败，返回 None，由调用方降级处理。
    """
    try:
        from llm_client import call_llm, extract_json_from_text
        from audit_prompt import build_file_audit_prompt
    except ImportError:
        return None

    # 仅在具备审核依据时调用 LLM
    has_audit_input = (
        (request.reviewBackground and request.reviewBackground.strip())
        or (request.backgroundFiles and len(request.backgroundFiles) > 0)
        or (request.checkConfig and request.checkConfig.parseRules)
    )
    if not has_audit_input:
        return None

    bg_files = []
    if request.backgroundFiles:
        for f in request.backgroundFiles:
            content = f.textContent or f.content or ""
            name = f.fileName or f.name or "背景文件"
            if content:
                bg_files.append({"fileName": name, "textContent": content})

    parse_rules = ""
    if request.checkConfig and request.checkConfig.parseRules:
        parse_rules = request.checkConfig.parseRules

    print(f"[file_parse] request.checkConfig: {request.checkConfig}")
    print(f"[file_parse] request.reviewBackground: {request.reviewBackground}")
    print(f"[file_parse] request.backgroundFiles: {request.backgroundFiles}")
    print(f"[file_parse] request.file: {request.file}")
    print(f"[file_parse] text_content: {text_content}")
    messages = build_file_audit_prompt(
        review_background=request.reviewBackground or "",
        background_files=bg_files,
        parse_rules=parse_rules,
        file_name=request.file.name if request.file else "",
        file_content=text_content,
    )

    try:
        response_text = call_llm(messages)
        audit_result = extract_json_from_text(response_text)
        print(f"[file_parse] audit_result: {audit_result}")
    except Exception as e:
        import traceback
        print(f"[file_parse] error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None

    # 规范化统一审核结果
    passed = audit_result.get("passed", False)
    if isinstance(passed, str):
        passed = passed.lower() in ("true", "1", "yes", "通过")

    return {
        "passed": bool(passed),
        "reason": str(audit_result.get("reason", "")) if not passed else "",
        "details": str(audit_result.get("details", "")),
    }


@app.post("/api/steps/file-parse")
async def file_parse(
    file: Optional[UploadFile] = File(None),
    stepId: str = Form(""),
    workflowId: str = Form(""),
    sessionId: str = Form(""),
    textContent: Optional[str] = Form(None),
    reviewBackground: Optional[str] = Form(None),
    parseRules: Optional[str] = Form(None),
    backgroundFiles: Optional[str] = Form(None),
):
    """
    审核步骤 - 文件解析接口
    支持 multipart/form-data 文件上传，也支持直接传入 textContent（向后兼容）。
    根据审核背景、背景技术文件、解析规则自动生成提示词，调用大模型执行审核。
    返回统一的审核步骤结果（JSON）：是否通过、不通过原因。
    """
    print(f"[file_parse] stepId={stepId}, file={file.filename if file else None}")
    start_time = time.time()

    text_content_result = ""
    file_name = None
    file_size = 0

    if file is not None:
        file_bytes = await file.read()
        file_name = file.filename
        file_size = len(file_bytes)
        text_content_result = parse_file(file_bytes, file_name or "")
    
    if not text_content_result and textContent:
        text_content_result = textContent

    bg_files_parsed = None
    if backgroundFiles:
        try:
            bg_files_parsed = json.loads(backgroundFiles)
        except json.JSONDecodeError:
            bg_files_parsed = None

    request = FileParseRequest(
        stepId=stepId,
        workflowId=workflowId,
        sessionId=sessionId,
        textContent=text_content_result,
        reviewBackground=reviewBackground,
        backgroundFiles=[BackgroundFileItem(**bf) for bf in bg_files_parsed] if bg_files_parsed else None,
        checkConfig=CheckConfig(parseRules=parseRules) if parseRules else None,
    )

    metadata = {
        "pageCount": 1,
        "author": "system",
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
    }
    if file_name:
        metadata["fileName"] = file_name
        metadata["fileSize"] = file_size

    audit_result = _run_file_audit_with_llm(request, text_content_result)

    duration_ms = int((time.time() - start_time) * 1000)

    if audit_result is not None:
        passed = audit_result["passed"]
        msg = "审核通过" if passed else f"审核未通过：{audit_result.get('reason', '')}"
        return {
            "success": passed,
            "code": 200 if passed else 400,
            "message": msg,
            "data": {
                "success": passed,
                "message": msg,
                "data": {
                    "textContent": text_content_result,
                    "metadata": metadata,
                    "auditResult": audit_result,
                },
                "duration": duration_ms,
            },
            "timestamp": int(time.time() * 1000),
        }

    return {
        "success": True,
        "code": 200,
        "message": "文件解析成功（未执行大模型审核）",
        "data": {
            "success": True,
            "message": "文件解析成功",
            "data": {
                "textContent": text_content_result,
                "metadata": metadata,
            },
            "duration": duration_ms,
        },
        "timestamp": int(time.time() * 1000),
    }


# ==================== 审核步骤 - 问答交互 API ====================

@app.post("/api/steps/qa-interaction")
def qa_interaction(request: QAInteractionRequest):
    """
    审核步骤 - 问答交互接口
    仅接收请求参数并构建返回，不做具体处理。
    """
    start_time = time.time()
    answer = request.answer or (str(request.userInput) if request.userInput is not None else "")
    question = request.questionConfig.question if request.questionConfig else ""

    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "success": True,
        "code": 200,
        "message": "问答交互完成",
        "data": {
            "success": True,
            "message": "问答交互完成",
            "data": {
                "question": question,
                "answer": answer,
                "validation": {
                    "isValid": True,
                    "score": 100,
                    "feedback": "回答符合预期",
                },
            },
            "duration": duration_ms,
        },
        "timestamp": int(time.time() * 1000),
    }


# ==================== 审核步骤 - 单选 API ====================

@app.post("/api/steps/single-select")
def single_select(request: SingleSelectRequest):
    """
    审核步骤 - 单选验证接口
    仅接收请求参数并构建返回，不做具体处理。
    """
    start_time = time.time()
    selected_value = request.selectedValue or (str(request.userInput) if request.userInput is not None else "")
    selected_label = ""
    if request.optionsConfig and request.optionsConfig.options:
        for opt in request.optionsConfig.options:
            if opt.value == selected_value:
                selected_label = opt.label
                break

    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "success": True,
        "code": 200,
        "message": "已选择",
        "data": {
            "success": True,
            "message": "已选择",
            "data": {
                "selectedValue": selected_value,
                "selectedLabel": selected_label,
                "isCorrect": None,
            },
            "duration": duration_ms,
        },
        "timestamp": int(time.time() * 1000),
    }


# ==================== 审核步骤 - 多选 API ====================

@app.post("/api/steps/multi-select")
def multi_select(request: MultiSelectRequest):
    """
    审核步骤 - 多选验证接口
    仅接收请求参数并构建返回，不做具体处理。
    """
    start_time = time.time()
    selected_values = request.selectedValues or []
    if not selected_values and request.userInput is not None:
        selected_values = list(request.userInput) if isinstance(request.userInput, (list, tuple)) else [str(request.userInput)]

    selected_labels = []
    if request.optionsConfig and request.optionsConfig.options:
        value_to_label = {opt.value: opt.label for opt in request.optionsConfig.options}
        selected_labels = [value_to_label.get(v, "") for v in selected_values]

    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "success": True,
        "code": 200,
        "message": "已选择",
        "data": {
            "success": True,
            "message": "已选择",
            "data": {
                "selectedValues": selected_values,
                "selectedLabels": selected_labels,
                "score": 100,
                "isFullyCorrect": None,
                "scoreDetails": {
                    "correctCount": len(selected_values),
                    "incorrectCount": 0,
                    "missedCount": 0,
                },
            },
            "duration": duration_ms,
        },
        "timestamp": int(time.time() * 1000),
    }


# ==================== 审核步骤 - 脚本检查 API ====================

@app.post("/api/steps/script-check")
def script_check(request: ScriptCheckRequest):
    """
    审核步骤 - 脚本执行检查接口
    仅接收请求参数并构建返回，不做具体处理。
    """
    start_time = time.time()
    script_content = request.script.content if request.script else ""
    script_language = request.script.language if request.script else "javascript"

    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "success": True,
        "code": 200,
        "message": "脚本检查完成",
        "data": {
            "success": True,
            "message": "脚本检查完成",
            "data": {
                "result": {"success": True},
                "stdout": "",
                "stderr": "",
                "executionTime": duration_ms,
                "passed": True,
                "checkDetails": [
                    {"name": "语法检查", "passed": True},
                    {"name": "逻辑验证", "passed": True},
                ],
            },
            "duration": duration_ms,
        },
        "timestamp": int(time.time() * 1000),
    }


# ==================== 审核步骤 - 子流程 API ====================

@app.post("/api/steps/sub-workflow")
def sub_workflow(request: SubWorkflowRequest):
    """
    审核步骤 - 子流程执行接口
    仅接收请求参数并构建返回，不做具体处理。
    """
    start_time = time.time()

    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "success": True,
        "code": 200,
        "message": "子流程执行完成",
        "data": {
            "success": True,
            "message": "子流程执行完成",
            "data": {
                "status": "completed",
                "totalSteps": 0,
                "completedSteps": 0,
                "stepResults": [],
                "overallResult": {
                    "success": True,
                    "passedSteps": 0,
                    "failedSteps": 0,
                },
            },
            "duration": duration_ms,
        },
        "timestamp": int(time.time() * 1000),
    }