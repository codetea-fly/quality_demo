import json
import re
from typing import Dict, Any, List

class ProcessGroupPromptGenerator:
    """
    精简版ISO过程组提示词生成器
    输入过程组名称，直接输出对应的提示词
    """
    
    def __init__(self, json_data: Dict[str, Any]):
        """
        初始化生成器
        
        Args:
            json_data: 包含过程域映射的JSON数据
        """
        self.json_data = json_data
        self.main_file = json_data.get("file", "GJB9001C")
        self.main_file_path = json_data.get('file_path')
    
    def extract_plain_text(self, file_path: str) -> str:
        """
        提取Markdown文件的纯文本内容
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            纯文本内容字符串
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            return content
            
        except FileNotFoundError:
            return f"错误：文件 {file_path} 未找到"
        except Exception as e:
            return f"错误：读取文件时出错 - {str(e)}"
        
    def extract_structured_text(self, file_path: str, query: str) -> Dict[str, List[str]]:
        """
        提取结构化的纯文本内容（按章节分组）
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            按章节分组的文本内容字典
        """
        plain_text = self.extract_plain_text(file_path)
        
        # 按章节分割内容
        sections = re.split(r'(?=^## )', plain_text, flags=re.MULTILINE)
        
        structured_content = []
        #current_section = "文档开头"
        
        for section in sections:
            if not section.strip():
                continue
            if query in section:
                structured_content.append(section)
        #     # # 提取章节标题
        #     # header_match = re.match(r'^(#+)\s+(.+)$', section, flags=re.MULTILINE)
        #     # if header_match:
        #     #     current_section = header_match.group(2).strip()
        #     #     # 移除标题行，保留内容
        #     #     content_start = section.find('\n', header_match.end())
        #     #     if content_start != -1:
        #     #         section_content = section[content_start:].strip()
        #     #     else:
        #     #         section_content = ""
        #     # else:
        #     #     section_content = section.strip()
            
        #     # if section_content:
        #     #     # 分割为段落
        #     #     paragraphs = [p.strip() for p in section_content.split('\n\n') if p.strip()]
        #     #     if paragraphs:
        #     #         structured_content[current_section] = paragraphs
        
        return structured_content

    def generate_prompt(self, process_group_name: str, background="", structure="标准程序文件格式", replace="") -> str:
        """
        生成过程组对应的提示词
        
        Args:
            process_group_name: ISO过程组名称
            
        Returns:
            生成的提示词字符串
        """
        # 查找目标过程组
        target_group = None
        for group in self.json_data.get("process_domains", []):
            if str(process_group_name) in group.get("name"):
                target_group = group
                break
        
        if not target_group:
            return f"错误：未找到名为 '{process_group_name}' 的过程组"
        
        # 收集参考文件
        reference_files = self._collect_reference_files(target_group)
        
        # 构建提示词
        prompt = self._build_prompt_template(target_group, reference_files,background,structure, replace)
        
        return prompt
    
    def _collect_reference_files(self, process_group: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        收集过程组的所有参考文件
        """
        files = []
        
        # 添加主文件
        files.append({
            "type": "总体要求",
            "file_name": self.main_file,
            "file_path": self.main_file_path,
            "charpter": process_group['charpter'],
            "description": f"过程组 '{process_group['name']}' 的总体要求"
        })
        
        # 递归收集过程域文件
        self._collect_domain_files(process_group.get("related_domains", []), files, 1)
        
        return files
    
    def _collect_domain_files(self, domains: List[Dict], files: List[Dict], level: int):
        """
        递归收集过程域文件
        """
        for domain in domains:
            if domain.get("file"):
                files.append({
                    "type": "细化要求",
                    "level": level,
                    "file_name": domain["file"],
                    "domain_name": domain["name"],
                    "file_path": domain['file_path'],
                    "description": f"层级{level}细化要求：{domain['name']}"
                })
            
            # 递归处理子过程域
            if domain.get("related_domains"):
                self._collect_domain_files(domain["related_domains"], files, level + 1)
    
    def _build_prompt_template(self, process_group: Dict[str, Any], reference_files: List[Dict], backgrond:str, structure:str, replace:str) -> str:
        """
        构建提示词模板
        """
        # 分离总体文件和细化文件
        main_files = [f for f in reference_files if f["type"] == "总体要求"]
        detail_files = [f for f in reference_files if f["type"] == "细化要求"]
        
        # 按层级排序细化文件
        detail_files.sort(key=lambda x: x["level"])
        
        prompt = f"""请根据以下参考文件，为过程组【{process_group['name']}】生成控制文件。

## 参考文件清单

### 总体要求文件(文件内容在<FileContent></FileContent>标签中)
{self._format_file_list(main_files)}

### 细化要求文件（文件内容在<DetailContent></DetailContent>标签中）
{self._format_hierarchical_files(detail_files)}

## 生成要求

1. **文件结构**：按照以下文件结构组织内容：{structure}
2. **层次关系**：体现从总体要求到具体细化的逻辑关系  
3. **技术要求**：严格遵循参考文件的技术规范
4. **可操作性**：提供具体的实施指南和检查要点
5. **组织背景**：按照以下组织背景调整文件内容的表述：{backgrond}
6. **术语替换**：按照以下规则替换术语：{replace}

请基于以上参考文件生成专业、实用的程序文件。"""

        return prompt
    
    def _format_file_list(self, files: List[Dict]) -> str:
        """格式化文件列表"""
        if not files:
            return "无总体要求文件"
        result = "\n"
        for f in files:
            charpter = "所有章节"
            if len(f['charpter']) != 0:
                charpter = f['charpter']
            result += f"以下<FileContent></FileContent>标签中为总体要求文件{self.main_file}，参考其中的{charpter}章节"
            result += "\n<FileContent>\n"
            contents = self.extract_structured_text(f['file_path'],charpter)
            for content in contents:
                result += content
                result += "\n"
            result += "\n</FileContent>"
        return result
        #return "\n<FileContent>".join([f"- {f['file_name']}：{f['description']}" for f in files]).join("</FileContent>")
    
    def _format_hierarchical_files(self, files: List[Dict]) -> str:
        """格式化层次化文件列表"""
        if not files:
            return "无细化要求文件"
        
        result = ""
        current_level = 0
        
        for file in files:
            if file["level"] > current_level:
                #result += f"\n层级 {file['level']}：\n"
                current_level = file["level"]
            #result += f"- {file['file_name']}（{file['domain_name']}）\n"
            result += "\n<DetailContent>\n"
            result += self.extract_plain_text(file['file_path'])
            result += "\n</DetailContent>"

        return result
    

# 使用示例
def main():
    """
    使用示例
    """
    # 示例JSON数据
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\knowledge.json','r',encoding='utf-8') as file:
        sample_json = json.load(file)
    
    # 创建生成器实例
    generator = ProcessGroupPromptGenerator(sample_json)
    
    # 生成提示词示例
    process_group_name = "不合格品控制"
    prompt = generator.generate_prompt(process_group_name)
    
    with open('C:\\Users\\29884\\Desktop\\北航课题\\demo\\example.txt','w', encoding='utf-8') as f:
        f.write(prompt)
    # test = generator.extract_structured_text("C:\\Users\\29884\\Desktop\\北航课题\\GJB 9001C-2017相关国家军用标准\\GJB9001\\GJB9001C.md")
    # print(test)

# 直接使用函数
def generate_prompt_from_json(json_data: Dict[str, Any], process_group_name: str, background:str, structure:str, replace:str) -> str:
    """
    一键生成提示词的便捷函数
    
    Args:
        json_data: JSON数据
        process_group_name: 过程组名称
        
    Returns:
        生成的提示词
    """
    generator = ProcessGroupPromptGenerator(json_data)
    return generator.generate_prompt(process_group_name, background, structure,replace)

if __name__ == "__main__":
    main()