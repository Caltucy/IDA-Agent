# 说明

## 前提须知

此分支后续开发迭代，请使用 Chainlit Python Web 快速开发框架，新手易学 https://docs.chainlit.io/get-started/overview

目前版本，登陆尚未完善，聊天记录需要配置登陆系统，请自行参考 https://docs.chainlit.io/data-persistence/history 开发

账户密码：

```
- admin
- ida2024
```

## 开发步骤

```
pip install -r requirements.txt

cp .env.example .env

python run_chainlit.py

```

## 环境变量

- `OPENAI_API_KEY`: 
- `OPENAI_API_BASE`:
- `OPENAI_MODEL_NAME`:
- `CHAINLIT_AUTH_SECRET`: Chainlit 密码验证器，使用 `chainlit create-secret` 生成