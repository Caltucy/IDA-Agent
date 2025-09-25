"use client";

import { useEffect, useMemo, useState } from "react";

export interface ChatSessionMeta {
  id: string;
  name: string;
  createdAt: number;
  updatedAt: number;
}

interface SidebarProps {
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreate: (session: ChatSessionMeta) => void;
  onDelete: (id: string) => void;
}

const SESSIONS_KEY = "chatSessions";

export default function Sidebar({ selectedId, onSelect, onCreate, onDelete }: SidebarProps) {
  const [sessions, setSessions] = useState<ChatSessionMeta[]>([]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(SESSIONS_KEY);
      if (raw) {
        const list = JSON.parse(raw) as ChatSessionMeta[];
        setSessions(Array.isArray(list) ? list : []);
      }
    } catch (e) {
      setSessions([]);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
  }, [sessions]);

  const ordered = useMemo(() => {
    return [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);
  }, [sessions]);

  const createSession = () => {
    const now = Date.now();
    const session: ChatSessionMeta = {
      id: crypto.randomUUID(),
      name: `新对话 ${new Date(now).toLocaleString()}`,
      createdAt: now,
      updatedAt: now,
    };
    setSessions(prev => [session, ...prev]);
    onCreate(session);
  };

  const deleteSession = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setSessions(prev => prev.filter(s => s.id !== id));
    // 删除对应的消息存档
    try { localStorage.removeItem(`chatMessages:${id}`); } catch {}
    onDelete(id);
  };

  const renameSession = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const current = sessions.find(s => s.id === id);
    if (!current) return;
    const name = prompt("重命名对话", current.name) || current.name;
    setSessions(prev => prev.map(s => s.id === id ? { ...s, name, updatedAt: Date.now() } : s));
  };

  return (
    <div className="w-64 flex-shrink-0 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 h-screen overflow-y-auto">
      <div className="p-3 flex items-center justify-between border-b border-gray-200 dark:border-gray-700">
        <span className="font-semibold">会话</span>
        <button
          onClick={createSession}
          className="px-2 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded"
        >
          新建
        </button>
      </div>
      <div>
        {ordered.length === 0 ? (
          <div className="p-4 text-sm text-gray-500">暂无会话，点击“新建”。</div>
        ) : (
          ordered.map(s => (
            <div
              key={s.id}
              onClick={() => onSelect(s.id)}
              className={`px-3 py-2 cursor-pointer flex items-center justify-between ${
                selectedId === s.id ? "bg-blue-50 dark:bg-gray-800" : "hover:bg-gray-100 dark:hover:bg-gray-800"
              }`}
            >
              <div className="min-w-0">
                <div className="text-sm font-medium truncate">{s.name}</div>
                <div className="text-xs text-gray-500 truncate">{new Date(s.updatedAt).toLocaleString()}</div>
              </div>
              <div className="flex items-center gap-1 ml-2">
                <button
                  onClick={(e) => renameSession(s.id, e)}
                  title="重命名"
                  className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-200"
                >✎</button>
                <button
                  onClick={(e) => deleteSession(s.id, e)}
                  title="删除"
                  className="text-red-500 hover:text-red-600"
                >×</button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}


