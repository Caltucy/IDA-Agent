# 图表生成API使用说明

## 概述

本项目已实现传统的图表生成方法：后端使用Python的Matplotlib库直接生成图表图片，然后通过API接口将图片流返回给前端显示。

## 工作流程

### 后端流程
1. 使用Matplotlib处理数据并绘制图表
2. 将图表渲染到内存中的字节流（bytes buffer）
3. 通过API接口返回图片流，设置正确的Content-Type为image/png

### 前端流程
1. 使用`<img>`标签显示图表
2. 将`src`属性指向后端的图片生成API地址
3. 自动处理加载状态和错误处理

## API接口

### 图表生成接口
- **URL**: `POST /api/generate-chart`
- **参数**:
  - `chart_data`: JSON字符串，包含图表数据
  - `chart_type`: 图表类型（bar/line/pie）
  - `title`: 图表标题
- **返回**: PNG格式的图片流

### 数据格式
```json
{
  "labels": ["一月", "二月", "三月", "四月", "五月"],
  "values": [10, 25, 15, 30, 20]
}
```

## 支持的图表类型

1. **柱状图 (bar)**: 使用蓝色主题色
2. **折线图 (line)**: 使用绿色主题色
3. **饼图 (pie)**: 自动计算百分比

## 安装和运行

### 后端依赖
确保安装了matplotlib：
```bash
pip install matplotlib>=3.7.0
```

### 启动服务
1. 启动后端服务：
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. 启动前端服务：
```bash
npm run dev
```

## 测试

运行测试脚本验证API：
```bash
python test_chart_api.py
```

## 特性

- ✅ 支持中文显示
- ✅ 高分辨率图片输出（300 DPI）
- ✅ 自动内存管理
- ✅ 错误处理和回退机制
- ✅ 响应式设计
- ✅ 加载状态显示

## 优势

1. **性能**: 后端生成图片，减少前端计算负担
2. **兼容性**: 使用标准HTML img标签，兼容性更好
3. **灵活性**: 可以轻松添加新的图表类型
4. **可扩展**: 支持更多matplotlib功能
5. **缓存**: 可以轻松实现图片缓存机制

## 注意事项

- 确保后端服务正在运行
- 图片会在内存中生成，注意内存使用
- 支持的文件格式：PNG
- 自动清理临时图片URL，避免内存泄漏




