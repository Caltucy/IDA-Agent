from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import os
import json
from typing import Optional
import tempfile
from .langgraph_workflow import process_query, process_query_streaming
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
    file: Optional[UploadFile] = File(None),
    messages_json: Optional[str] = Form(None)
):
    file_path = None
    messages = []
    
    # 解析消息历史
    if messages_json:
        try:
            messages = json.loads(messages_json)
        except Exception as e:
            return {"error": f"解析消息历史错误: {str(e)}"}
    
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
        result = process_query(instruction, file_path, messages)
        
        return result
    except Exception as e:
        return {"error": f"处理请求时出错: {str(e)}"}

@app.post("/api/process-stream")
async def process_request_stream(
    instruction: str = Form(...),
    file: Optional[UploadFile] = File(None),
    messages_json: Optional[str] = Form(None)
):
    file_path = None
    messages = []
    
    # 解析消息历史
    if messages_json:
        try:
            messages = json.loads(messages_json)
        except Exception as e:
            return {"error": f"解析消息历史错误: {str(e)}"}
    
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
    
    # 流式处理函数
    async def generate_stream():
        try:
            async for chunk in process_query_streaming(instruction, file_path, messages):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(), 
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )