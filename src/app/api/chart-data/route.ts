import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';

const execAsync = promisify(exec);

export async function GET(req: NextRequest) {
  try {
    console.log('开始执行MATLAB脚本...');
    
    // 获取MATLAB脚本的绝对路径
    const matlabScriptPath = path.join(process.cwd(), 'create_data.m');
    
    // 检查MATLAB脚本是否存在
    if (!fs.existsSync(matlabScriptPath)) {
      return NextResponse.json({ 
        error: 'MATLAB脚本不存在', 
        path: matlabScriptPath 
      }, { status: 404 });
    }
    
    // 执行MATLAB脚本
    // 注意：这里假设MATLAB已安装并在PATH中
    const matlabCommand = `matlab -batch "run('${matlabScriptPath}')"`;
    console.log('执行命令:', matlabCommand);
    
    const { stdout, stderr } = await execAsync(matlabCommand, {
      timeout: 60000, // 60秒超时
      cwd: process.cwd()
    });
    
    console.log('MATLAB执行输出:', stdout);
    if (stderr) {
      console.log('MATLAB执行错误:', stderr);
    }
    
    // 检查输出目录
    const outputDir = path.join(process.cwd(), 'output');
    if (!fs.existsSync(outputDir)) {
      return NextResponse.json({ 
        error: '输出目录不存在', 
        output: stdout,
        stderr: stderr 
      }, { status: 500 });
    }
    
    // 读取生成的数据文件
    const dataFile = path.join(outputDir, 'data.json');
    if (!fs.existsSync(dataFile)) {
      return NextResponse.json({ 
        error: '数据文件未生成', 
        output: stdout,
        stderr: stderr 
      }, { status: 500 });
    }
    
    // 读取JSON数据
    const jsonData = fs.readFileSync(dataFile, 'utf-8');
    const data = JSON.parse(jsonData);
    
    // 读取状态文件
    const statusFile = path.join(outputDir, 'status.txt');
    let status = '';
    if (fs.existsSync(statusFile)) {
      status = fs.readFileSync(statusFile, 'utf-8');
    }
    
    // 检查生成的图片文件
    const imageFiles = [
      'time_series.png',
      'bar_chart.png', 
      'scatter_plot.png',
      'combined_chart.png'
    ];
    
    const availableImages = imageFiles.filter(file => 
      fs.existsSync(path.join(outputDir, file))
    );
    
    // 将图片转换为base64编码
    const images: { [key: string]: string } = {};
    for (const imageFile of availableImages) {
      const imagePath = path.join(outputDir, imageFile);
      const imageBuffer = fs.readFileSync(imagePath);
      const base64Image = imageBuffer.toString('base64');
      images[imageFile] = `data:image/png;base64,${base64Image}`;
    }
    
    // 返回完整的数据响应
    return NextResponse.json({
      success: true,
      data: data,
      images: images,
      status: status,
      availableImages: availableImages,
      timestamp: new Date().toISOString()
    });
    
  } catch (error: any) {
    console.error('执行MATLAB脚本时出错:', error);
    
    // 检查是否有错误文件
    const errorFile = path.join(process.cwd(), 'output', 'error.txt');
    let errorMessage = error.message;
    
    if (fs.existsSync(errorFile)) {
      const errorContent = fs.readFileSync(errorFile, 'utf-8');
      errorMessage = errorContent;
    }
    
    return NextResponse.json({ 
      error: '执行MATLAB脚本失败',
      details: errorMessage,
      timestamp: new Date().toISOString()
    }, { status: 500 });
  }
}

// 支持POST请求，可以传递参数
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { parameters } = body;
    
    console.log('收到POST请求，参数:', parameters);
    
    // 这里可以根据参数修改MATLAB脚本的执行
    // 例如：传递不同的数据生成参数
    
    // 执行GET逻辑
    return await GET(req);
    
  } catch (error: any) {
    console.error('处理POST请求时出错:', error);
    return NextResponse.json({ 
      error: '处理请求失败',
      details: error.message 
    }, { status: 500 });
  }
}
