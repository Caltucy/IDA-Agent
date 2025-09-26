# API 配置说明

## 问题描述
系统出现 "API Key配额已耗尽" 错误，这是因为缺少正确的API配置。

## 解决方案

### 1. 创建环境变量文件
在项目根目录创建 `.env` 文件，内容如下：

```env
# OpenAI API 配置
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_BASE_URL=https://bi.ganjiuwanshi.com/v1
OPENAI_MODEL_NAME=gpt-4o

# 其他配置
PYTHONIOENCODING=utf-8
```

### 2. 获取API Key
您需要从 `https://bi.ganjiuwanshi.com` 获取有效的API Key，并替换 `.env` 文件中的 `your_actual_api_key_here`。

### 3. 重启服务
配置完成后，重启后端服务：

```bash
cd backend
python run.py
```

## 当前状态
- ✅ 已修复代码中的API配置问题
- ⏳ 需要您手动创建 `.env` 文件并添加有效的API Key
- ⏳ 需要重启服务以应用新配置

## 注意事项
- 请确保API Key有效且有足够的配额
- 如果仍有问题，请检查网络连接和API服务状态




