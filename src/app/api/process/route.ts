import { NextRequest, NextResponse } from 'next/server';

// Python后端API地址：从环境变量读取，默认本地
const BACKEND_BASE = (process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');
const PYTHON_API_URL = `${BACKEND_BASE}/api/process`;

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    let instruction = formData.get('instruction') as string;
    const file = formData.get('file') as File | null;
    const history = formData.get('history') as string | null;
    
    // instruction 允许为空；为空时使用默认分析指令
    if (!instruction || instruction.trim().length === 0) {
      instruction = '请基于我上传的文件进行基础分析，输出 report，并返回一个或多个 charts（type 为 bar/line，data 含 labels 与 values，可附 title 与 seriesName）。不要弹出图形窗口。';
    }
    
    // 创建新的FormData对象发送到Python后端
    const newFormData = new FormData();
    newFormData.append('instruction', instruction);
    
    // 如果有文件，处理文件
    if (file) {
      newFormData.append('file', file);
    }
    if (history) {
      newFormData.append('history', history);
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
    // 将 charts 暂存，供聊天组件使用（简单方案）
    try {
      // 仅在服务端，不能直接访问 sessionStorage。此处把原样数据返回给前端，由前端自行保存。
    } catch {}
    return NextResponse.json(data);
  } catch (error) {
    console.error('处理请求时出错:', error);
    return NextResponse.json({ error: `处理请求时出错: ${error}` }, { status: 500 });
  }
}