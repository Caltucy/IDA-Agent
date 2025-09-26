# MATLAB集成说明

本项目实现了MATLAB脚本与Node.js后端的集成，允许在无人值守的情况下执行MATLAB计算并生成图表。

## 架构概述

```
MATLAB脚本 → Node.js API → 前端组件
    ↓           ↓           ↓
create_data.m → /api/chart-data → MatlabChartRenderer
```

## 组件说明

### 1. MATLAB脚本 (create_data.m)

**功能：**
- 生成时间序列数据（sin, cos, sin(2t)）
- 创建分类数据
- 生成散点图数据
- 计算统计信息
- 保存数据为JSON格式
- 生成多种图表并保存为PNG文件

**输出文件：**
- `output/data.json` - 包含所有数据的JSON文件
- `output/time_series.png` - 时间序列图
- `output/bar_chart.png` - 柱状图
- `output/scatter_plot.png` - 散点图
- `output/combined_chart.png` - 综合图表
- `output/status.txt` - 执行状态文件

### 2. Node.js API路由 (/api/chart-data)

**功能：**
- 执行MATLAB脚本
- 读取生成的数据文件
- 将图片转换为base64编码
- 返回完整的JSON响应

**API端点：**
- `GET /api/chart-data` - 执行MATLAB脚本并返回数据
- `POST /api/chart-data` - 支持传递参数（预留功能）

**响应格式：**
```json
{
  "success": true,
  "data": {
    "time_series": { "t": [...], "y1": [...], "y2": [...], "y3": [...] },
    "categorical": { "categories": [...], "values": [...] },
    "scatter": { "x": [...], "y": [...] },
    "statistics": { "mean_y1": 0, "std_y1": 1, ... },
    "timestamp": "2024-01-01 12:00:00"
  },
  "images": {
    "time_series.png": "data:image/png;base64,...",
    "bar_chart.png": "data:image/png;base64,...",
    ...
  },
  "status": "MATLAB脚本执行成功...",
  "availableImages": ["time_series.png", "bar_chart.png", ...],
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 3. 前端组件 (MatlabChartRenderer)

**功能：**
- 显示MATLAB执行状态
- 展示数据统计信息
- 渲染生成的图表
- 显示数据表格
- 提供重新执行功能

**特性：**
- 自动加载数据
- 错误处理和重试机制
- 响应式设计
- 实时状态更新

## 使用方法

### 1. 环境要求

- MATLAB R2018b或更高版本
- Node.js 18或更高版本
- 确保MATLAB在系统PATH中可用

### 2. 启动应用

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 3. 测试MATLAB集成

访问测试页面：`http://localhost:3000/matlab-test`

### 4. 在聊天界面中使用

1. 打开主聊天界面
2. 点击"显示MATLAB数据"按钮
3. 系统将自动执行MATLAB脚本并显示结果

## 自定义和扩展

### 修改MATLAB脚本

编辑 `create_data.m` 文件来：
- 更改数据生成逻辑
- 添加新的图表类型
- 修改输出格式

### 扩展API功能

在 `src/app/api/chart-data/route.ts` 中：
- 添加参数验证
- 实现缓存机制
- 添加错误恢复功能

### 自定义前端显示

在 `src/components/MatlabChartRenderer.tsx` 中：
- 添加新的图表类型支持
- 实现数据导出功能
- 添加交互式图表

## 故障排除

### 常见问题

1. **MATLAB未找到**
   - 确保MATLAB已安装
   - 检查MATLAB是否在PATH中
   - 尝试使用完整路径：`C:\Program Files\MATLAB\R2023a\bin\matlab.exe`

2. **权限错误**
   - 确保Node.js有权限执行MATLAB
   - 检查输出目录的写入权限

3. **超时错误**
   - 增加API路由中的超时时间
   - 优化MATLAB脚本性能

4. **图片显示问题**
   - 检查图片文件是否正确生成
   - 验证base64编码是否正确

### 调试技巧

1. 查看控制台日志
2. 检查 `output/` 目录中的文件
3. 手动执行MATLAB脚本测试
4. 使用测试页面验证功能

## 性能优化

1. **缓存机制**：实现结果缓存避免重复执行
2. **异步处理**：使用队列处理长时间运行的脚本
3. **资源管理**：及时清理临时文件
4. **错误恢复**：实现自动重试机制

## 安全考虑

1. **输入验证**：验证所有输入参数
2. **路径安全**：防止路径遍历攻击
3. **资源限制**：限制执行时间和内存使用
4. **权限控制**：限制MATLAB脚本的执行权限






