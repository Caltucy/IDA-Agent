import { NextRequest, NextResponse } from 'next/server';
import { writeFile } from 'fs/promises';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { mkdir } from 'fs/promises';

// Python后端API地址
const PYTHON_API_URL = 'http://localhost:8000/api/process';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const instruction = formData.get('instruction') as string;
    const file = formData.get('file') as File | null;
    const messagesJson = formData.get('messages_json') as string | null;
    
    if (!instruction) {
      return NextResponse.json({ error: '指令不能为空' }, { status: 400 });
    }
    
    // 创建新的FormData对象发送到Python后端
    const newFormData = new FormData();
    newFormData.append('instruction', instruction);
    
    // 如果有消息历史记录，添加到请求中
    if (messagesJson) {
      newFormData.append('messages_json', messagesJson);
    }
    
    // 如果有文件，处理文件
    if (file) {
      newFormData.append('file', file);
    }
    
    // 发送请求到Python后端
    const response = await fetch(PYTHON_API_URL, {
      method: 'POST',
      body: newFormData,
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json({ error: `Python后端错误: ${errorText}` }, { status: response.status });
    }
    
    const data = await response.json();
    
    // 如果后端返回了文件路径，将其添加到响应中
    if (data.file_path) {
      data.filePath = data.file_path;
    }
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('处理请求时出错:', error);
    return NextResponse.json({ error: `处理请求时出错: ${error}` }, { status: 500 });
  }
}