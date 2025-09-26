import { NextRequest, NextResponse } from 'next/server';

// Python后端API地址：从环境变量读取，默认本地
const BACKEND_BASE = (process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');
const PYTHON_CHART_API_URL = `${BACKEND_BASE}/api/generate-chart`;

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    
    // 创建新的FormData对象发送到Python后端
    const newFormData = new FormData();
    newFormData.append('chart_data', formData.get('chart_data') as string);
    newFormData.append('chart_type', formData.get('chart_type') as string || 'bar');
    newFormData.append('title', formData.get('title') as string || '图表');
    
    // 发送请求到Python后端
    const response = await fetch(PYTHON_CHART_API_URL, {
      method: 'POST',
      body: newFormData,
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json({ error: `Python后端图表生成错误: ${errorText}` }, { status: response.status });
    }
    
    // 返回图片流
    const imageBuffer = await response.arrayBuffer();
    return new NextResponse(imageBuffer, {
      status: 200,
      headers: {
        'Content-Type': 'image/png',
        'Content-Disposition': 'inline; filename=chart.png'
      }
    });
    
  } catch (error) {
    console.error('图表生成请求处理时出错:', error);
    return NextResponse.json({ error: `处理图表生成请求时出错: ${error}` }, { status: 500 });
  }
}



