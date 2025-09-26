"use client";

import { useState } from "react";
import Chat from "../components/Chat";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-900">
      {/* 顶部标题栏 */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-center">
          <h1 className="text-2xl font-bold text-gray-100">数据分析智能助手</h1>
        </div>
      </header>

      {/* 主内容区域 */}
      <div className="max-w-4xl mx-auto p-6">
        <Chat />
      </div>
    </div>
  );
}
