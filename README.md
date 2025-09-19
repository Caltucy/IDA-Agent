# 数据分析智能助手

这是一个使用 [Next.js](https://nextjs.org) 构建的数据分析智能助手项目。

## ✨ 项目特色

- **智能分析**: 输入您的数据查询，AI 将为您生成深入的分析报告。
- **图表可视化**: 自动将数据转换成易于理解的图表，支持多种图表类型。
- **一体化架构**: 基于 Next.js 构建，前后端逻辑清晰地整合在同一个项目中。

## 🚀 快速开始

首先，确保您已经安装了 [Node.js](https://nodejs.org/)。

然后，运行开发服务器：

```bash
npm run dev
# 或者
yarn dev
# 或者
pnpm dev
```

在您的浏览器中打开 [http://localhost:3000](http://localhost:3000) 查看结果。

您可以开始编辑 `src/app/page.tsx` 文件来修改主页面。当您编辑文件时，页面会自动更新。

## 环境变量

在运行项目之前，您需要在项目根目录创建一个 `.env.local` 文件，并填入您的 OpenAI API 密钥等信息：

```
OPENAI_API_KEY=YOUR_API_KEY
OPENAI_API_BASE=YOUR_API_BASE_URL
```

## 📖 了解更多

想了解更多关于 Next.js 的信息，请查看以下资源：

- [Next.js 官方文档](https://nextjs.org/docs) - 了解 Next.js 的特性和 API。
- [学习 Next.js](https://nextjs.org/learn) - 一个交互式的 Next.js 教程。

## 部署

部署您的 Next.js 应用最简单的方式是使用 [Vercel 平台](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme)，它由 Next.js 的创建者开发。

查看我们的 [Next.js 部署文档](https://nextjs.org/docs/app/building-your-application/deploying) 了解更多细节。
