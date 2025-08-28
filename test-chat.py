import requests
import json
import sys

def stream_generate(prompt, model="gemma-3n-E4B-it-Q4_K_M"):
    url = "http://127.0.0.1:8000/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True
    }
    
    try:
        print(f"正在连接到服务器: {url}")
        print(f"发送请求: {json.dumps(payload, ensure_ascii=False)}")
        
        with requests.post(url, json=payload, stream=True, timeout=30) as response:
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                print(f"错误响应: {response.text}")
                return
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    print(f"收到数据: {line}")  # 调试信息
                    
                    if line.startswith('data: '):
                        data = line[6:]  # 去掉 'data: ' 前缀
                        if data == '[DONE]':
                            print("\n流式生成完成")
                            break
                        try:
                            chunk = json.loads(data)
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    print(delta['content'], end='', flush=True)
                        except json.JSONDecodeError as e:
                            print(f"JSON解析错误: {e}")
                            continue
    
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")

# 使用示例
if __name__ == "__main__":
    print("开始测试流式生成...")
    stream_generate("请解释人工智能的概念")
    print("\n测试完成")