#!/usr/bin/env python3
"""
🧠 Qwen3-VL-32B-Thinking 提取维修手册文字
"""

import os, json, base64, requests
from pathlib import Path

API_KEY = os.getenv('SILICONFLOW_API_KEY')
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL = "Qwen/Qwen3-VL-32B-Thinking"

def extract_image(image_path):
    """用视觉模型提取图片文字"""
    print(f"🧠 处理: {image_path.name}")
    
    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    resp = requests.post(API_URL, headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }, json={
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "提取这张维修手册的所有文字，保持格式，只输出文字内容"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        }],
        "temperature": 0.3,
        "max_tokens": 4000
    }, timeout=180)
    
    return resp.json()['choices'][0]['message']['content']

def main():
    # 扫描待处理文件
    for src in ['uploads', 'raw_manuals']:
        path = Path(src)
        if not path.exists():
            continue
        
        for f in path.glob('*'):
            if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                try:
                    text = extract_image(f)
                    # 保存提取的文字
                    out = Path("knowledge_texts") / f"{f.stem}.txt"
                    out.write_text(text, encoding='utf-8')
                    print(f"  ✅ {len(text)}字 → {out}")
                    
                    # 移动原文件到processed
                    f.rename(Path("processed") / f.name)
                    
                except Exception as e:
                    print(f"  ❌ {f.name}: {e}")

if __name__ == "__main__":
    Path("knowledge_texts").mkdir(exist_ok=True)
    Path("processed").mkdir(exist_ok=True)
    main()
