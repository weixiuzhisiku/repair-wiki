#!/usr/bin/env python3
import os, json, re, requests
from pathlib import Path

SILICONFLOW_KEY = os.environ.get("SILICONFLOW_KEY", "")
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

def extract_text(filepath):
    text = ""
    if filepath.endswith('.pdf'):
        try:
            import fitz
            doc = fitz.open(filepath)
            for page in doc:
                text += page.get_text()
        except Exception as e:
            print(f"PDF error: {e}")
    elif filepath.endswith('.docx'):
        try:
            from docx import Document
            doc = Document(filepath)
            text = "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            print(f"DOCX error: {e}")
    return text[:12000]

def parse_with_32b(text, filename):
    if not SILICONFLOW_KEY:
        return []
    prompt = f"""解析以下维修手册为JSON格式：
{text[:8000]}

输出格式：[{{"id":"1","title":"故障","content":"步骤...","source":"{filename}"}}]"""
    try:
        r = requests.post(API_URL, headers={"Authorization": f"Bearer {SILICONFLOW_KEY}"},
            json={"model": "Qwen/Qwen3-32B", "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2, "max_tokens": 4000}, timeout=180)
        content = r.json()["choices"][0]["message"]["content"]
        json_match = re.search(r'$$\s*\{.*\}\s*$$', content, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else []
    except Exception as e:
        print(f"API error: {e}")
        return []

def main():
    upload_dir = Path("uploads")
    if not upload_dir.exists():
        Path("uploads").mkdir(exist_ok=True)
        json.dump({"chunks": [], "metadata": {"version": "1.0", "total": 0}}, 
            open("knowledge_base.json", 'w'), ensure_ascii=False, indent=2)
        return
    all_chunks = []
    for f in upload_dir.iterdir():
        if f.suffix.lower() in ['.pdf', '.docx', '.txt']:
            print(f"Processing: {f.name}")
            text = extract_text(str(f))
            if len(text) > 100:
                chunks = parse_with_32b(text, f.name)
                all_chunks.extend(chunks)
                print(f"  Got {len(chunks)} chunks")
    kb = {"chunks": all_chunks, "metadata": {"version": "1.0", "total": len(all_chunks), "source": "Qwen3-32B"}}
    with open("knowledge_base.json", 'w', encoding='utf-8') as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    print(f"Total: {len(all_chunks)} chunks")

if __name__ == "__main__":
    main()
