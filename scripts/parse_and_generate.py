#!/usr/bin/env python3
"""
自动解析上传的维修手册，调用硅基流动32B生成知识库
"""

import os
import json
import re
import requests
from pathlib import Path

SILICONFLOW_KEY = os.environ.get("SILICONFLOW_KEY", "")
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

def extract_text(filepath):
    """从PDF/DOCX提取文字"""
    text = ""
    
    if filepath.endswith('.pdf'):
        try:
            import fitz
            doc = fitz.open(filepath)
            for page in doc:
                text += page.get_text()
        except Exception as e:
            print(f"PDF提取错误: {e}")
            
    elif filepath.endswith('.docx'):
        try:
            from docx import Document
            doc = Document(filepath)
            text = "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            print(f"DOCX提取错误: {e}")
            
    elif filepath.endswith('.txt'):
        text = Path(filepath).read_text(encoding='utf-8')
        
    return text[:12000]  # 限制长度

def parse_with_32b(text, filename):
    """调用硅基流动Qwen3-32B解析"""
    
    if not SILICONFLOW_KEY:
        print("错误: 未配置API密钥")
        return []
    
    prompt = f"""你是一个专业的维修文档解析专家。请将以下维修手册内容解析为结构化的JSON格式。

【文件名】{filename}

【维修手册内容】
{text[:8000]}

【要求】
1. 识别所有故障现象，每个作为独立条目
2. 提取具体的排查步骤（1. 2. 3. 编号）
3. 保留关键参数和注意事项
4. 输出标准JSON数组，不要任何解释文字

【输出格式】
[
  {{
    "id": "唯一ID",
    "title": "故障现象标题",
    "content": "详细步骤...",
    "source": "{filename}"
  }}
]"""

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {SILICONFLOW_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "Qwen/Qwen3-32B",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 4000
            },
            timeout=180  # 32B需要更长时间
        )
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # 提取JSON部分
        json_match = re.search(r'$$\s*\{.*\}\s*$$', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            # 尝试清理后解析
            clean = content.strip()
            if clean.startswith('[') and clean.endswith(']'):
                return json.loads(clean)
            else:
                print(f"无法解析JSON，原始内容: {content[:500]}")
                return [{"id": "parse_error", "title": "解析失败", "content": content[:300], "source": filename}]
                
    except Exception as e:
        print(f"API调用错误: {e}")
        return [{"id": "api_error", "title": "API错误", "content": str(e), "source": filename}]

def main():
    upload_dir = Path("uploads")
    output_file = Path("knowledge_base.json")
    
    if not upload_dir.exists():
        print("创建uploads目录")
        upload_dir.mkdir(exist_ok=True)
        # 初始化空知识库
        empty_kb = {"chunks": [], "metadata": {"version": "1.0", "total": 0}}
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(empty_kb, f, ensure_ascii=False, indent=2)
        return
    
    # 加载现有知识库
    all_chunks = []
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                all_chunks = existing.get("chunks", [])
                print(f"现有知识库: {len(all_chunks)} 条")
        except:
            pass
    
    # 处理新上传的文件
    processed = 0
    for filepath in upload_dir.iterdir():
        if filepath.suffix.lower() in ['.pdf', '.docx', '.txt']:
            print(f"\n处理: {filepath.name}")
            
            text = extract_text(str(filepath))
            if not text or len(text) < 100:
                print(f"  跳过: 内容太短或提取失败")
                continue
            
            print(f"  提取文字: {len(text)} 字符")
            
            # 调用32B解析
            chunks = parse_with_32b(text, filepath.name)
            print(f"  解析结果: {len(chunks)} 条知识")
            
            all_chunks.extend(chunks)
            processed += 1
            
            # 可选：处理后归档文件
            # filepath.rename(Path("processed") / filepath.name)
    
    # 去重（简单按title去重）
    seen = set()
    unique_chunks = []
    for c in all_chunks:
        title = c.get("title", "")
        if title and title not in seen:
            seen.add(title)
            unique_chunks.append(c)
    
    # 保存知识库
    knowledge_base = {
        "chunks": unique_chunks,
        "metadata": {
            "version": "1.0",
            "total": len(unique_chunks),
            "generated_by": "硅基流动Qwen3-32B",
            "last_update": str(Path().stat().st_mtime)
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*40}")
    print(f"处理完成: {processed} 个文件")
    print(f"知识库总计: {len(unique_chunks)} 条（去重后）")
    print(f"保存到: {output_file}")
    print(f"{'='*40}")

if __name__ == "__main__":
    main()
