"use client";

import { useEffect } from "react";

// 演示数据组件，用于初始化一些示例文档
export default function DemoData() {
  useEffect(() => {
    // 检查是否已有文档，如果没有则创建一些演示文档
    try {
      const existing = localStorage.getItem("ida_documents");
      if (!existing || JSON.parse(existing).length === 0) {
        const demoDocuments = [
          {
            id: "demo-1",
            name: "销售数据分析",
            type: "excel",
            size: 1024000,
            uploadTime: new Date().toLocaleString(),
            content: "包含2023年销售数据的Excel文件"
          },
          {
            id: "demo-2", 
            name: "用户行为报告",
            type: "csv",
            size: 512000,
            uploadTime: new Date().toLocaleString(),
            content: "用户访问和购买行为数据"
          },
          {
            id: "demo-3",
            name: "财务季度报表",
            type: "excel", 
            size: 2048000,
            uploadTime: new Date().toLocaleString(),
            content: "Q3财务数据和趋势分析"
          }
        ];
        localStorage.setItem("ida_documents", JSON.stringify(demoDocuments));
      }
    } catch (error) {
      console.error("初始化演示数据失败:", error);
    }
  }, []);

  return null; // 这是一个无UI组件
}





