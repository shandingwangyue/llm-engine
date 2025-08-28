#!/usr/bin/env python3
"""
简单的应用状态检查脚本
"""

import requests
import time

def main():
    print("🔍 检查应用状态...")
    
    try:
        # 尝试连接健康检查接口
        response = requests.get('http://localhost:8000/api/v1/health', timeout=2)
        print(f"✅ 连接成功! 状态码: {response.status_code}")
        print(f"响应内容: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 应用可能未启动或端口被占用")
    except requests.exceptions.Timeout:
        print("❌ 连接超时 - 应用可能正在启动中")
    except Exception as e:
        print(f"❌ 连接异常: {e}")
    
    return False

if __name__ == "__main__":
    main()