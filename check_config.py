#!/usr/bin/env python3
"""
配置检查工具 - 不修改代码的解决方案
"""
import os
import sys
import requests
from urllib.parse import urljoin

def check_environment():
    """检查环境变量配置"""
    print("=== 环境变量检查 ===")
    
    # 检查必要的环境变量
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("OPENAI_MODEL_NAME") 
    api_key = os.getenv("OPENAI_API_KEY")
    
    print(f"OPENAI_BASE_URL: {base_url or '❌ 未设置'}")
    print(f"OPENAI_MODEL_NAME: {model_name or '❌ 未设置'}")
    print(f"OPENAI_API_KEY: {'✅ 已设置' if api_key else '❌ 未设置'}")
    
    return bool(base_url and model_name and api_key)

def check_api_connection():
    """检查API连接"""
    print("\n=== API连接检查 ===")
    
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not base_url or not api_key:
        print("❌ 环境变量未完整设置，无法测试连接")
        return False
    
    try:
        # 测试API端点
        test_url = urljoin(base_url, "/models")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"测试连接: {test_url}")
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ API连接正常")
            return True
        elif response.status_code == 401:
            print("❌ API Key无效或配额已耗尽")
            return False
        else:
            print(f"❌ API返回错误: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接失败: {e}")
        return False

def provide_solutions():
    """提供解决方案"""
    print("\n=== 解决方案 ===")
    
    print("1. 设置环境变量 (PowerShell):")
    print('   $env:OPENAI_BASE_URL = "https://bi.ganjiuwanshi.com/v1"')
    print('   $env:OPENAI_MODEL_NAME = "gpt-4o"')
    print('   $env:OPENAI_API_KEY = "your_actual_api_key"')
    print()
    
    print("2. 使用启动脚本:")
    print("   PowerShell: .\\start_server_with_env.ps1")
    print("   批处理: start_server.bat")
    print()
    
    print("3. 检查API Key:")
    print("   - 访问 https://bi.ganjiuwanshi.com")
    print("   - 确认API Key有效且有足够配额")
    print("   - 如有需要，购买更多配额")

def main():
    """主函数"""
    print("数据分析服务配置检查工具")
    print("=" * 40)
    
    # 检查环境变量
    env_ok = check_environment()
    
    if env_ok:
        # 检查API连接
        api_ok = check_api_connection()
        
        if api_ok:
            print("\n✅ 配置检查通过，可以启动服务")
            print("运行命令: cd backend && python run.py")
        else:
            print("\n❌ API连接失败，请检查API Key和配额")
            provide_solutions()
    else:
        print("\n❌ 环境变量配置不完整")
        provide_solutions()

if __name__ == "__main__":
    main()




