"""
文件解析模块 - 支持 txt, pdf, docx 格式解析
"""
import os


def parse_file(file_bytes: bytes, filename: str) -> str:
    """
    解析文件内容，返回文本字符串。
    
    Args:
        file_bytes: 文件二进制内容
        filename: 文件名（用于判断格式）
    
    Returns:
        解析后的文本内容，解析失败或不支持的格式返回空字符串
    """
    if not filename:
        return ""
    
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == ".txt":
        return _parse_txt(file_bytes)
    elif ext == ".pdf":
        return _parse_pdf(file_bytes)
    elif ext == ".docx":
        return _parse_docx(file_bytes)
    else:
        return ""


def _parse_txt(file_bytes: bytes) -> str:
    """解析 txt 文件"""
    for encoding in ["utf-8", "gbk", "gb2312", "latin-1"]:
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return ""


def _parse_pdf(file_bytes: bytes) -> str:
    """解析 pdf 文件"""
    try:
        import pdfplumber
        import io
        
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        pass
    
    try:
        import PyPDF2
        import io
        
        text_parts = []
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        pass
    
    return ""


def _parse_docx(file_bytes: bytes) -> str:
    """解析 docx 文件"""
    try:
        import docx
        import io
        
        doc = docx.Document(io.BytesIO(file_bytes))
        text_parts = []
        for para in doc.paragraphs:
            if para.text:
                text_parts.append(para.text)
        return "\n".join(text_parts)
    except ImportError:
        return ""
    except Exception:
        return ""
