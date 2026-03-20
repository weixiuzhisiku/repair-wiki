import os
import json
import base64
import requests
from datetime import datetime

# ================= 配置 =================
UPLOADS_DIR = "uploads"
OUTPUT_FILE = "knowledge_base.json"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL_NAME = "Qwen/Qwen3-VL-32B"

def get_image_base64(image_path):
    """读取图片并转换为 base64"""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded_string}"
    except Exception as e:
        print(f"读取图片失败 {image_path}: {e}")
        return None

def call_vl_model(image_path):
    """调用视觉大模型 API"""
    api_key = os.getenv("SILICONFLOW_KEY")
    if not api_key:
        print(" 错误: 未找到 SILICONFLOW_KEY 环境变量")
        return None

    base64_image = get_image_base64(image_path)
    if not base64_image:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请分析这张图片，提取其中的所有文字内容。如果图片包含表格，请用 Markdown 格式输出表格。请使用中文回答。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": base64_image
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.7
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"API 请求失败: {e}")
        return None

def main():
    if not os.path.exists(UPLOADS_DIR):
        print(f"目录不存在: {UPLOADS_DIR}")
        return

    results = []
    for filename in os.listdir(UPLOADS_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            file_path = os.path.join(UPLOADS_DIR, filename)
            print(f"正在处理: {filename}")
            content = call_vl_model(file_path)
            if content:
                results.append({
                    "filename": filename,
                    "content": content,
                    "processed_at": datetime.now().isoformat()
                })

    if results:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"处理完成, 结果已保存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
