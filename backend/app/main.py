from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Optional
import tempfile
from .langgraph_workflow import process_query
import time

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "DAagent API is running"}

@app.post("/api/process")
async def process_request(
    instruction: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    file_path = None
    
    # 如果上传了文件，保存到项目 data/ 目录
    if file:
        try:
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
        except Exception as e:
            return {"error": f"文件处理错误: {str(e)}"}
    
    # 调用LangGraph工作流处理请求
    try:
        result = process_query(instruction, file_path)
        
        return result
    except Exception as e:
        return {"error": f"处理请求时出错: {str(e)}"}