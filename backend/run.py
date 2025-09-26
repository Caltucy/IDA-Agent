import uvicorn
import signal
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """优雅关闭信号处理器"""
    logger.info("收到关闭信号，正在优雅关闭服务...")
    sys.exit(0)

if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("启动数据分析服务...")
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            log_level="info",
            access_log=True,
            # 优化配置
            workers=1,  # 单进程模式，避免多进程问题
            loop="asyncio",  # 使用asyncio事件循环
            timeout_keep_alive=30,  # 保持连接超时
            timeout_graceful_shutdown=30,  # 优雅关闭超时
        )
    except KeyboardInterrupt:
        logger.info("服务被用户中断")
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        sys.exit(1)