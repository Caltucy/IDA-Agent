#!/usr/bin/env python3
"""
Chainlit 应用启动脚本
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import chainlit
        import langchain
        import langgraph
        logger.info("✅ 所有依赖已正确安装")
        return True
    except ImportError as e:
        logger.error(f"❌ 缺少依赖: {e}")
        return False

def install_dependencies():
    """安装依赖"""
    logger.info("📦 正在安装依赖...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        logger.info("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 依赖安装失败: {e}")
        return False

def setup_environment():
    """设置环境变量"""
    # 确保 data 目录存在
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    logger.info(f"📁 数据目录: {data_dir}")
    
    # 检查 .env 文件
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        logger.warning("⚠️ 未找到 .env 文件，请确保配置了 OPENAI_API_KEY")
        # 创建示例 .env 文件
        with open(env_file, "w") as f:
            f.write("# OpenAI API 配置\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
            f.write("OPENAI_MODEL_NAME=gpt-4o\n")
            f.write("\n# 其他配置\n")
            f.write("PYTHONIOENCODING=utf-8\n")
        logger.info(f"📝 已创建示例 .env 文件: {env_file}")

def run_chainlit_app():
    """运行 Chainlit 应用"""
    app_file = Path(__file__).parent / "chainlit_app.py"
    
    if not app_file.exists():
        logger.error(f"❌ 应用文件不存在: {app_file}")
        return False
    
    logger.info("🚀 启动 Chainlit 应用...")
    logger.info("📍 应用将在以下地址运行:")
    logger.info("   本地访问: http://localhost:8080")
    logger.info("   网络访问: http://0.0.0.0:8080")
    logger.info("")
    logger.info("💡 使用 Ctrl+C 停止应用")
    
    try:
        # 使用 chainlit run 命令启动应用
        cmd = [
            "chainlit", "run", str(app_file),
            "--host", "0.0.0.0",
            "--port", "8080",
            "--headless"  # 无头模式，不自动打开浏览器
        ]
        
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 启动应用失败: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("\n🛑 应用已停止")
        return True

def main():
    """主函数"""
    logger.info("🤖 IDA Agent - Chainlit 版本")
    logger.info("=" * 50)
    
    # 切换到脚本目录
    os.chdir(Path(__file__).parent)
    
    # 设置环境
    setup_environment()
    
    # 检查依赖
    if not check_dependencies():
        if not install_dependencies():
            logger.error("❌ 无法安装依赖，请手动运行: pip install -r requirements.txt")
            sys.exit(1)
    
    # 运行应用
    if not run_chainlit_app():
        sys.exit(1)

if __name__ == "__main__":
    main()
