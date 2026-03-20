#!/usr/bin/env python3
"""
生成可搜索的向量索引
"""

import json, re, math
from pathlib import Path

def text_to_vec(text):
    """中文向量"""
    chars = re.findall(r'[\u4e00-\u9fff]', text)
    vec = {}
    for c in chars:
        vec[c] = vec.get(c, 0) + 1
    for i in range(len(chars)-1):
        w = chars[i] + chars[i+1]
        vec[w] = vec.get(w, 0) + 1
    return vec

def main():
    docs = []
    
    # 加载所有文字
    for txt in Path("knowledge_texts").glob("*.txt"):
        text = txt.read_text(encoding='utf-8')
        docs.append({
            "id": txt.stem,
            "text": text[:2000],
            "vec": text_to_vec(text),
            "source": str(txt)
        })
    
    # 构建索引（只存关键词，不存完整向量节省空间）
    index = {
        "version": "2.0",
        "total": len(docs),
        "docs": []
    }
    
    for d in docs:
        # 提取高频词
        keywords = sorted(d['vec'].items(), key=lambda x: x[1], reverse=True)[:30]
        index['docs'].append({
            "id": d['id'],
            "text": d['text'],
            "keywords": dict(keywords),
            "source": d['source']
        })
    
    Path("knowledge_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    print(f"✅ 索引完成: {len(docs)} 条")

if __name__ == "__main__":
    main()
