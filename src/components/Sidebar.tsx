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
  const [query, setQuery] = useState("");

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

  // 监听 storage 以便跨标签或其他组件更新时刷新侧边栏
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === SESSIONS_KEY && e.newValue) {
        try {
          const list = JSON.parse(e.newValue) as ChatSessionMeta[];
          if (Array.isArray(list)) setSessions(list);
        } catch {}
      }
    };
    window.addEventListener("storage", handler);
    // 同标签页内：监听聊天消息更新事件，刷新列表时间戳
    const syncHandler = (e: any) => {
      const { sessionId } = e.detail || {};
      if (!sessionId) return;
      setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, updatedAt: Date.now() } : s));
    };
    window.addEventListener('chat-messages-updated', syncHandler as EventListener);
    return () => {
      window.removeEventListener("storage", handler);
      window.removeEventListener('chat-messages-updated', syncHandler as EventListener);
    };
  }, []);

  const ordered = useMemo(() => {
    const base = [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);
    if (!query.trim()) return base;
    const q = query.trim().toLowerCase();
    return base.filter(s => s.name.toLowerCase().includes(q));
  }, [sessions, query]);

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
    <div className="w-72 flex-shrink-0 border-r border-purple-200 dark:border-purple-800 bg-white dark:bg-gray-900 h-screen overflow-y-auto">
      {/* 顶部工具栏 */}
      <div className="p-3 border-b border-purple-200 dark:border-purple-800 bg-purple-50/60 dark:bg-purple-900/20">
        <div className="flex items-center justify-between mb-2">
          <span className="font-semibold text-purple-700 dark:text-purple-200">会话</span>
          <button
            onClick={createSession}
            onDoubleClick={createSession}
            className="px-3 py-1.5 text-sm bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600 text-white rounded-full shadow-sm active:scale-[0.98] transition"
            title="新建对话（双击快速连建）"
          >
            + 新建
          </button>
        </div>
        <div className="relative">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索会话..."
            className="w-full px-3 py-2 text-sm rounded-full border border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-purple-400"
          />
          {query && (
            <button
              className="absolute right-2 top-1/2 -translate-y-1/2 text-purple-500 hover:text-purple-700 text-sm"
              onClick={() => setQuery("")}
              aria-label="清空搜索"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* 会话列表 */}
      <div>
        {ordered.length === 0 ? (
          <div className="p-4 text-sm text-gray-500">暂无会话，点击“新建”。</div>
        ) : (
          ordered.map(s => (
            <SessionItem
              key={s.id}
              session={s}
              active={selectedId === s.id}
              onClick={() => onSelect(s.id)}
              onRename={(e) => renameSession(s.id, e)}
              onDelete={(e) => deleteSession(s.id, e)}
            />
          ))
        )}
      </div>
    </div>
  );
}

/* 内联小组件，便于和文件放同目录管理。但你也可以拆到独立文件。*/
function SessionItem({
  session,
  active,
  onClick,
  onRename,
  onDelete,
}: {
  session: ChatSessionMeta;
  active: boolean;
  onClick: () => void;
  onRename: (e: React.MouseEvent) => void;
  onDelete: (e: React.MouseEvent) => void;
}) {
  const [preview, setPreview] = useState<string>("");
  const [count, setCount] = useState<number>(0);

  useEffect(() => {
    const load = () => {
      try {
        const raw: any = JSON.parse(localStorage.getItem(`chatMessages:${session.id}`) || "null");
        if (Array.isArray(raw) && raw.length) {
          setCount(raw.length);
          const last = raw[raw.length - 1];
          const text: string = (last?.content || "").toString();
          setPreview(text.replace(/\s+/g, " ").slice(0, 28));
        } else {
          setCount(0);
          setPreview("（暂无消息）");
        }
      } catch {
        setCount(0);
        setPreview("（暂无消息）");
      }
    };
    load();
    const handler = (e: StorageEvent) => {
      if (e.key === `chatMessages:${session.id}`) {
        load();
      }
    };
    window.addEventListener('storage', handler);
    // 同标签页内也监听自定义事件
    const localHandler = (e: any) => {
      const { sessionId } = e.detail || {};
      if (sessionId === session.id) load();
    };
    window.addEventListener('chat-messages-updated', localHandler as EventListener);
    return () => {
      window.removeEventListener('storage', handler);
      window.removeEventListener('chat-messages-updated', localHandler as EventListener);
    };
  }, [session.id, session.updatedAt]);

  return (
    <div
      onClick={onClick}
      className={`px-3 py-2 cursor-pointer group flex items-start justify-between transition-colors ${
        active ? "bg-purple-50 dark:bg-gray-800" : "hover:bg-purple-50 dark:hover:bg-gray-800"
      }`}
      title={session.name}
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <div className="text-sm font-medium truncate text-gray-900 dark:text-gray-100">{session.name}</div>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-200 whitespace-nowrap">
            {count > 0 ? `有 ${count} 条消息` : '无消息'}
          </span>

        </div>
        <div className="text-xs text-gray-500 truncate">
          {preview}
        </div>
        <div className="text-[11px] text-gray-400">
          {new Date(session.updatedAt).toLocaleString()}
        </div>
      </div>
      <div className="flex items-center gap-1 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={onRename}
          title="重命名"
          className="text-gray-500 hover:text-purple-700 dark:hover:text-gray-200 text-sm px-1"
          aria-label="重命名"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
            <path d="M13.586 3.586a2 2 0 112.828 2.828l-9.192 9.192a2 2 0 01-.878.505l-3.12.78a.5.5 0 01-.606-.606l.78-3.12a2 2 0 01.505-.878l9.192-9.192z"/>
          </svg>
        </button>
        <button
          onClick={onDelete}
          title="删除"
          className="text-red-500 hover:text-red-600 text-sm px-1"
          aria-label="删除"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
            <path fillRule="evenodd" d="M6 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            <path d="M4 5h12l-1 12a2 2 0 01-2 2H7a2 2 0 01-2-2L4 5zM8 2a2 2 0 00-2 2H4a1 1 0 100 2h12a1 1 0 100-2h-2a2 2 0 00-2-2H8z" />
          </svg>
        </button>
      </div>
    </div>
  );
}