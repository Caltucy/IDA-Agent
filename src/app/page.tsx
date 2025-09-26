"use client";

import ChatInterface from "../components/ChatInterface";
import Sidebar, { type ChatSessionMeta } from "../components/Sidebar";
import { useEffect, useMemo, useState } from "react";

export default function Home() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // 首次加载选择最近一次会话或创建新会话占位
  useEffect(() => {
    const raw = localStorage.getItem("chatSessions");
    if (raw) {
      try {
        const list = JSON.parse(raw) as ChatSessionMeta[];
        if (Array.isArray(list) && list.length > 0) {
          const latest = [...list].sort((a, b) => b.updatedAt - a.updatedAt)[0];
          setSelectedId(latest.id);
          return;
        }
      } catch {}
    }
    // 若没有会话，创建一个临时ID但不写入列表，等待侧边栏创建
    setSelectedId(null);
  }, []);

  const handleSelect = (id: string) => {
    setSelectedId(id);
  };

  const handleCreate = (session: ChatSessionMeta) => {
    setSelectedId(session.id);
  };

  const handleDelete = (id: string) => {
    if (selectedId === id) {
      // 选择其他会话（若存在）
      try {
        const raw = localStorage.getItem("chatSessions");
        const list = raw ? (JSON.parse(raw) as ChatSessionMeta[]) : [];
        const remain = list.filter(s => s.id !== id);
        setSelectedId(remain.length ? remain.sort((a, b) => b.updatedAt - a.updatedAt)[0].id : null);
      } catch {
        setSelectedId(null);
      }
    }
  };

  return (
    <div className="flex min-h-screen bg-purple-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
      <Sidebar selectedId={selectedId} onSelect={handleSelect} onCreate={handleCreate} onDelete={handleDelete} />
      <main className="flex-1 p-4 sm:p-8">
        <div className="flex justify-center items-center mb-6">
          <h1 className="text-3xl sm:text-4xl font-bold text-center text-purple-700 dark:text-purple-300">数据分析代理</h1>
        </div>
        {selectedId ? (
          <ChatInterface key={selectedId} sessionId={selectedId} />
        ) : (
          <div className="w-full max-w-3xl mx-auto h-[80vh] flex items-center justify-center text-gray-500">
            在左侧点击“新建”开始一个新的对话
          </div>
        )}
      </main>
    </div>
  );
}
