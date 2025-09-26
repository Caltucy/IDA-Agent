from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.exception_handlers import http_exception_handler
import os
from typing import Optional
import tempfile
from .langgraph_workflow import process_query, clear_cache
import time
import io
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import json
import logging
import asyncio
import signal
import sys

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="数据分析服务",
    description="基于LangGraph的数据分析API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 应用生命周期管理
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("数据分析服务启动中...")
    # 清理之前的缓存
    clear_cache()
    logger.info("服务启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("数据分析服务正在关闭...")
    # 清理缓存
    clear_cache()
    logger.info("服务已关闭")

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}")
    return {"error": f"服务器内部错误: {str(exc)}", "status": 500}

@app.get("/")
async def root():
    """根路径，返回服务状态"""
    return {
        "message": "数据分析服务正在运行",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "数据分析服务"
    }

@app.post("/api/clear-cache")
async def clear_cache_endpoint():
    """清理缓存端点"""
    try:
        clear_cache()
        return {"message": "缓存已清理", "status": "success"}
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")

@app.post("/api/process")
async def process_request(
    instruction: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """处理数据分析请求"""
    try:
        logger.info(f"收到处理请求: {instruction[:100]}...")
        
        file_path = None
        
        # 如果上传了文件，保存到项目 data/ 目录
        if file:
            try:
                # 检查文件大小限制（100MB）
                if file.size and file.size > 100 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="文件大小超过100MB限制")
                
                # 确保 data 目录存在（项目根目录下）
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                data_dir = os.path.join(base_dir, 'data')
                os.makedirs(data_dir, exist_ok=True)

                # 生成保存文件名，避免覆盖
                original_name = os.path.basename(file.filename)
                name, ext = os.path.splitext(original_name)
                timestamp = int(time.time())
                safe_name = f"{name}_{timestamp}{ext}"
                file_path = os.path.join(data_dir, safe_name)

                # 写入上传内容
                content = await file.read()
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                logger.info(f"文件保存成功: {file_path}")
                
            except Exception as e:
                logger.error(f"文件处理错误: {e}")
                raise HTTPException(status_code=400, detail=f"文件处理错误: {str(e)}")
        
        # 调用LangGraph工作流处理请求
        try:
            result = process_query(instruction, file_path)
            logger.info("请求处理完成")
            return result
        except Exception as e:
            logger.error(f"处理请求时出错: {e}")
            raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"未预期的错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@app.post("/api/generate-chart")
async def generate_chart(
    chart_data: str = Form(...),
    chart_type: str = Form("bar"),
    title: str = Form("图表")
):
    """生成图表图片并返回图片流"""
    try:
        # 解析图表数据
        data = json.loads(chart_data)
        
        # 创建图表
        plt.figure(figsize=(10, 6))
        
        # 配置中文字体支持
        import platform
        system = platform.system()
        
        # 尝试配置中文字体
        try:
            if system == 'Windows':
                # Windows系统字体配置
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'Microsoft YaHei UI', 'SimHei', 'SimSun', 'KaiTi', 'FangSong', 'DejaVu Sans']
            elif system == 'Darwin':  # macOS
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti TC', 'Heiti SC', 'STHeiti', 'PingFang SC', 'PingFang TC', 'DejaVu Sans']
            else:  # Linux
                plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'Noto Sans CJK TC', 'DejaVu Sans']
        except Exception:
            # 如果配置失败，使用默认配置
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 10
        
        if chart_type == "bar":
            # 柱状图
            labels = data.get('labels', [])
            values = data.get('values', [])
            plt.bar(labels, values, color='#6366f1', alpha=0.8)
            plt.xlabel('类别')
            plt.ylabel('数值')
        elif chart_type == "line":
            # 折线图
            labels = data.get('labels', [])
            values = data.get('values', [])
            plt.plot(labels, values, marker='o', color='#10b981', linewidth=2, markersize=6)
            plt.xlabel('类别')
            plt.ylabel('数值')
        elif chart_type == "pie":
            # 饼图
            labels = data.get('labels', [])
            values = data.get('values', [])
            plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        else:
            # 默认柱状图
            labels = data.get('labels', [])
            values = data.get('values', [])
            plt.bar(labels, values, color='#6366f1', alpha=0.8)
            plt.xlabel('类别')
            plt.ylabel('数值')
        
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # 将图表保存到内存中的字节流
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()  # 关闭图表以释放内存
        
        # 返回图片流
        return StreamingResponse(
            io.BytesIO(img_buffer.getvalue()),
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename={title}.png"}
        )
        
    except Exception as e:
        # 如果出错，返回错误图片
        plt.figure(figsize=(8, 4))
        plt.text(0.5, 0.5, f'图表生成错误: {str(e)}', 
                ha='center', va='center', fontsize=12, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral"))
        plt.axis('off')
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return StreamingResponse(
            io.BytesIO(img_buffer.getvalue()),
            media_type="image/png"
        )