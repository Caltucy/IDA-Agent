# MATLAB集成使用示例

## 快速开始

### 1. 基本使用

```typescript
// 在React组件中使用
import MatlabChartRenderer from './components/MatlabChartRenderer';

function MyComponent() {
  return (
    <div>
      <h1>MATLAB数据分析</h1>
      <MatlabChartRenderer />
    </div>
  );
}
```

### 2. 通过API直接获取数据

```javascript
// 获取MATLAB数据
async function getMatlabData() {
  try {
    const response = await fetch('/api/chart-data');
    const data = await response.json();
    
    if (data.success) {
      console.log('时间序列数据:', data.data.time_series);
      console.log('统计信息:', data.data.statistics);
      console.log('可用图片:', data.availableImages);
    }
  } catch (error) {
    console.error('获取数据失败:', error);
  }
}
```

### 3. 自定义MATLAB脚本参数

```typescript
// 发送POST请求传递参数
async function executeMatlabWithParams(params: any) {
  const response = await fetch('/api/chart-data', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      parameters: params
    })
  });
  
  return await response.json();
}
```

## 数据格式说明

### 时间序列数据
```json
{
  "time_series": {
    "t": [0, 0.1, 0.2, ...],      // 时间点
    "y1": [0, 0.0998, 0.1987, ...], // sin(t) + 噪声
    "y2": [1, 0.9950, 0.9801, ...], // cos(t) + 噪声
    "y3": [0, 0.1987, 0.3894, ...]   // sin(2t) + 噪声
  }
}
```

### 分类数据
```json
{
  "categorical": {
    "categories": ["A", "B", "C", "D", "E"],
    "values": [23, 45, 56, 78, 32]
  }
}
```

### 散点图数据
```json
{
  "scatter": {
    "x": [-1.2, 0.5, 2.1, ...],  // X坐标
    "y": [-2.1, 1.2, 4.3, ...]   // Y坐标
  }
}
```

### 统计信息
```json
{
  "statistics": {
    "mean_y1": 0.0234,           // Y1均值
    "std_y1": 0.9876,            // Y1标准差
    "mean_y2": -0.0123,          // Y2均值
    "std_y2": 1.0234,            // Y2标准差
    "correlation": 0.8765        // 相关系数
  }
}
```

## 实际应用场景

### 1. 科学数据分析
```matlab
% 在create_data.m中修改数据生成逻辑
% 例如：分析实验数据
experimental_data = load('experiment_results.mat');
processed_data = preprocess(experimental_data);
results = analyze(processed_data);
```

### 2. 金融数据可视化
```matlab
% 生成股票价格数据
dates = datetime(2024,1,1):days(1):datetime(2024,12,31);
prices = generate_stock_prices(length(dates));
returns = diff(prices) ./ prices(1:end-1);
```

### 3. 工程计算
```matlab
% 结构分析
loads = [100, 200, 150, 300];  % 载荷
stresses = calculate_stress(loads);
safety_factors = yield_strength ./ stresses;
```

## 高级功能

### 1. 批量处理
```typescript
// 处理多个数据集
async function processMultipleDatasets() {
  const datasets = ['dataset1', 'dataset2', 'dataset3'];
  const results = [];
  
  for (const dataset of datasets) {
    const result = await executeMatlabWithParams({ dataset });
    results.push(result);
  }
  
  return results;
}
```

### 2. 实时监控
```typescript
// 定期更新数据
useEffect(() => {
  const interval = setInterval(async () => {
    const data = await getMatlabData();
    updateDisplay(data);
  }, 30000); // 每30秒更新一次
  
  return () => clearInterval(interval);
}, []);
```

### 3. 数据导出
```typescript
// 导出MATLAB数据
function exportMatlabData(data: any) {
  const csvContent = convertToCSV(data);
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = 'matlab_data.csv';
  link.click();
}
```

## 错误处理

### 1. 网络错误
```typescript
async function robustGetData() {
  let retries = 3;
  
  while (retries > 0) {
    try {
      const data = await getMatlabData();
      return data;
    } catch (error) {
      retries--;
      if (retries === 0) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
}
```

### 2. MATLAB执行错误
```typescript
// 检查MATLAB执行状态
function checkMatlabStatus(data: any) {
  if (!data.success) {
    console.error('MATLAB执行失败:', data.error);
    return false;
  }
  
  if (data.availableImages.length === 0) {
    console.warn('未生成任何图片');
    return false;
  }
  
  return true;
}
```

## 性能优化建议

1. **缓存结果**：避免重复执行相同的MATLAB脚本
2. **异步处理**：使用Web Workers处理大量数据
3. **懒加载**：只在需要时加载图片
4. **压缩数据**：对大型数据集进行压缩传输

## 部署注意事项

1. **环境变量**：设置正确的MATLAB路径
2. **权限设置**：确保Node.js有执行MATLAB的权限
3. **资源限制**：设置适当的内存和时间限制
4. **监控日志**：记录MATLAB执行日志用于调试






