import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  try {
    console.log('返回测试MATLAB数据...');
    
    // 返回模拟的MATLAB数据，不实际执行MATLAB
    const mockData = {
      success: true,
      data: {
        time_series: {
          t: Array.from({ length: 101 }, (_, i) => i * 0.1),
          y1: Array.from({ length: 101 }, (_, i) => Math.sin(i * 0.1) + 0.1 * Math.random()),
          y2: Array.from({ length: 101 }, (_, i) => Math.cos(i * 0.1) + 0.1 * Math.random()),
          y3: Array.from({ length: 101 }, (_, i) => Math.sin(2 * i * 0.1) + 0.1 * Math.random())
        },
        categorical: {
          categories: ['A', 'B', 'C', 'D', 'E'],
          values: [23, 45, 56, 78, 32]
        },
        scatter: {
          x: Array.from({ length: 100 }, () => Math.random() * 4 - 2),
          y: Array.from({ length: 100 }, (_, i) => 2 * Math.random() * 4 - 2 + Math.random())
        },
        statistics: {
          mean_y1: 0.0234,
          std_y1: 0.9876,
          mean_y2: -0.0123,
          std_y2: 1.0234,
          correlation: 0.8765
        },
        timestamp: new Date().toLocaleString('zh-CN')
      },
      images: {
        'time_series.png': 'data:image/svg+xml;base64,' + Buffer.from(`
          <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="300" fill="#f0f0f0"/>
            <text x="200" y="150" text-anchor="middle" font-family="Arial" font-size="16" fill="#333">
              时间序列图 (模拟)
            </text>
            <text x="200" y="180" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">
              实际使用时将显示MATLAB生成的图表
            </text>
          </svg>
        `).toString('base64'),
        'bar_chart.png': 'data:image/svg+xml;base64,' + Buffer.from(`
          <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="300" fill="#f0f0f0"/>
            <text x="200" y="150" text-anchor="middle" font-family="Arial" font-size="16" fill="#333">
              柱状图 (模拟)
            </text>
            <text x="200" y="180" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">
              实际使用时将显示MATLAB生成的图表
            </text>
          </svg>
        `).toString('base64'),
        'scatter_plot.png': 'data:image/svg+xml;base64,' + Buffer.from(`
          <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="300" fill="#f0f0f0"/>
            <text x="200" y="150" text-anchor="middle" font-family="Arial" font-size="16" fill="#333">
              散点图 (模拟)
            </text>
            <text x="200" y="180" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">
              实际使用时将显示MATLAB生成的图表
            </text>
          </svg>
        `).toString('base64'),
        'combined_chart.png': 'data:image/svg+xml;base64,' + Buffer.from(`
          <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="300" fill="#f0f0f0"/>
            <text x="200" y="150" text-anchor="middle" font-family="Arial" font-size="16" fill="#333">
              综合图表 (模拟)
            </text>
            <text x="200" y="180" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">
              实际使用时将显示MATLAB生成的图表
            </text>
          </svg>
        `).toString('base64')
      },
      status: 'MATLAB脚本执行成功 (测试模式)\n执行时间: ' + new Date().toLocaleString('zh-CN') + '\n生成文件:\n- data.json\n- time_series.png\n- bar_chart.png\n- scatter_plot.png\n- combined_chart.png',
      availableImages: ['time_series.png', 'bar_chart.png', 'scatter_plot.png', 'combined_chart.png'],
      timestamp: new Date().toISOString()
    };
    
    return NextResponse.json(mockData);
    
  } catch (error: any) {
    console.error('返回测试数据时出错:', error);
    
    return NextResponse.json({ 
      error: '返回测试数据失败',
      details: error.message,
      timestamp: new Date().toISOString()
    }, { status: 500 });
  }
}







