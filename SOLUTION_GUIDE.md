# API配额耗尽问题解决方案

## 问题分析
从日志中可以看到错误信息：
```
ERROR:app.langgraph_workflow:LLM调用最终失败: Error code: 401 - {'success': False, 'message': 'API Key配额已耗尽'}
```

## 根本原因
1. **API配置不完整**: 代码中缺少 `base_url` 和 `api_key` 的正确配置
2. **环境变量未设置**: 缺少必要的环境变量配置
3. **API Key可能无效或配额不足**

## 已完成的修复

### ✅ 1. 修复代码配置
已更新 `backend/app/langgraph_workflow.py` 中的 `ChatOpenAI` 配置：
```python
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"), 
    api_key=os.getenv("OPENAI_API_KEY", ""),
    base_url=os.getenv("OPENAI_BASE_URL", "https://bi.ganjiuwanshi.com/v1"),
    temperature=0,
    max_retries=3,
    request_timeout=60,
    max_tokens=4000
)
```

### ✅ 2. 创建环境变量设置脚本
已创建 `set_env.bat` 文件来设置环境变量。

## 解决步骤

### 步骤1: 设置环境变量
运行以下命令设置环境变量：
```bash
# Windows PowerShell
$env:OPENAI_BASE_URL="https://bi.ganjiuwanshi.com/v1"
$env:OPENAI_MODEL_NAME="gpt-4o"

# 或者使用批处理文件
set_env.bat
```

### 步骤2: 验证API Key
确保您的API Key有效且有足够配额：
1. 访问 `https://bi.ganjiuwanshi.com`
2. 检查API Key状态和配额
3. 如有需要，购买更多配额或获取新的API Key

### 步骤3: 重启服务
```bash
cd backend
python run.py
```

## 测试验证

### 运行测试脚本
```bash
python test_api_config.py
```

预期输出：
```
=== API配置测试 ===
API Key: 已设置
Base URL: https://bi.ganjiuwanshi.com/v1
Model: gpt-4o

✅ API配置看起来正确
```

### 测试API连接
如果配置正确，服务启动后应该不再出现401错误。

## 故障排除

### 如果仍然出现401错误：
1. **检查API Key**: 确保API Key有效且未过期
2. **检查配额**: 确认API Key有足够的调用配额
3. **检查网络**: 确保能正常访问 `https://bi.ganjiuwanshi.com`
4. **检查服务状态**: 确认API服务正常运行

### 如果出现其他错误：
1. **网络超时**: 检查网络连接
2. **模型不可用**: 尝试更换模型名称
3. **权限问题**: 检查API Key权限设置

## 长期解决方案

### 1. 创建 .env 文件
在项目根目录创建 `.env` 文件：
```env
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_BASE_URL=https://bi.ganjiuwanshi.com/v1
OPENAI_MODEL_NAME=gpt-4o
```

### 2. 使用环境变量管理
建议使用专业的环境变量管理工具，如：
- Windows: 系统环境变量设置
- 开发环境: `.env` 文件 + `python-dotenv`

### 3. 监控和日志
- 定期检查API使用情况
- 设置配额告警
- 监控错误日志

## 联系支持
如果问题仍然存在，请联系：
- API服务提供商技术支持
- 检查服务状态页面
- 查看最新文档和更新




