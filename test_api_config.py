#!/usr/bin/env python3
"""
测试API配置的简单脚本
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_api_config():
    """测试API配置"""
    print("=== API配置测试 ===")
    
    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("OPENAI_MODEL_NAME")
    
    print(f"API Key: {'已设置' if api_key and api_key != 'your_api_key_here' else '未设置或使用默认值'}")
    print(f"Base URL: {base_url}")
    print(f"Model: {model_name}")
    
    if not api_key or api_key == 'your_api_key_here':
        print("\n❌ 错误: 请设置有效的 OPENAI_API_KEY")
        print("请在 .env 文件中设置正确的API Key")
        return False
    
    if not base_url:
        print("\n❌ 错误: 请设置 OPENAI_BASE_URL")
        return False
    
    print("\n✅ API配置看起来正确")
    return True

if __name__ == "__main__":
    test_api_config()




