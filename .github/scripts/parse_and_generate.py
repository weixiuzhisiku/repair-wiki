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

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请详细分析这张维修手册图片或文档截图，提取出故障现象、原因分析和维修步骤。请用中文输出，并保持结构清晰。"
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
        "temperature": 0.7,
        "max_tokens": 1024
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"API 请求失败: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def main():
    print("🚀 开始处理上传的文件...")
    
    if not os.path.exists(UPLOADS_DIR):
        print(f" 目录 {UPLOADS_DIR} 不存在")
        return

    knowledge_db = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                knowledge_db = json.load(f)
        except:
            print(" 无法读取现有知识库，将创建新的")

    image_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.gif')
    new_entries = 0

    for filename in os.listdir(UPLOADS_DIR):
        if filename.lower().endswith(image_extensions):
            filepath = os.path.join(UPLOADS_DIR, filename)
            print(f"🔍 正在处理: {filename}")
            
            if filename in knowledge_db:
                print(f"   ➡️ 已存在，跳过")
                continue

            analysis = call_vl_model(filepath)
            if analysis:
                knowledge_db[filename] = {
                    "source": f"{UPLOADS_DIR}/{filename}",
                    "analysis": analysis,
                    "processed_at": datetime.now().isoformat()
                }
                new_entries += 1
                print(f"   ✅ 成功解析")
            else:
                print(f"   ❌ 解析失败")

    if new_entries > 0:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(knowledge_db, f, ensure_ascii=False, indent=2)
        print(f"🎉 处理完成！新增 {new_entries} 个条目，已保存到 {OUTPUT_FILE}")
    else:
        print("📭 没有新文件需要处理")

if __name__ == "__main__":
    main()
