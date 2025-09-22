# 数据分析智能助手

这是一个使用 [Next.js](https://nextjs.org) 构建的数据分析智能助手项目，配合 Python 后端提供强大的数据分析能力。

## ✨ 项目特色

- **智能分析**: 输入您的数据查询，AI 将为您生成深入的分析报告。
- **图表可视化**: 自动将数据转换成易于理解的图表，支持多种图表类型。
- **一体化架构**: 前端基于 Next.js 构建，后端使用 Python FastAPI，提供完整的数据分析解决方案。

## 🚀 快速开始

### 前端启动

首先，确保您已经安装了 [Node.js](https://nodejs.org/)。

然后，安装项目依赖：

```bash
npm install
# 或者
yarn install
# 或者
pnpm install
```

接着，运行前端开发服务器：

```bash
npm run dev
# 或者
yarn dev
# 或者
pnpm dev
```

在您的浏览器中打开 [http://localhost:3000](http://localhost:3000) 查看前端页面。

您可以开始编辑 `src/app/page.tsx` 文件来修改主页面。当您编辑文件时，页面会自动更新。

### 后端启动

本项目需要同时运行 Python 后端服务。确保您已安装 Python 3.8+ 和所需依赖：

```bash
cd backend
pip install -r requirements.txt
python run.py
```

后端服务将在 [http://localhost:8000](http://localhost:8000) 启动。

## 环境变量

在运行项目之前，您需要在项目根目录创建一个 `.env` 文件，并填入以下环境变量：

```
OPENAI_API_KEY=YOUR_API_KEY
OPENAI_API_BASE=YOUR_API_BASE_URL
BACKEND_URL=http://localhost:8000
NODE_ENV=development
```

您可以参考项目根目录下的 `.env.template` 文件进行配置。

项目同时需要前端和后端服务同时运行才能正常工作。请确保两个服务都已启动。

## 📖 了解更多

想了解更多关于 Next.js 的信息，请查看以下资源：

- [Next.js 官方文档](https://nextjs.org/docs) - 了解 Next.js 的特性和 API。
- [学习 Next.js](https://nextjs.org/learn) - 一个交互式的 Next.js 教程。

## 部署

部署您的 Next.js 应用最简单的方式是使用 [Vercel 平台](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme)，它由 Next.js 的创建者开发。

查看我们的 [Next.js 部署文档](https://nextjs.org/docs/app/building-your-application/deploying) 了解更多细节。
