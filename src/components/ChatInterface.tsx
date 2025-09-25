"use client";

import { useState, useRef, useEffect } from "react";
import ChatMessage from "./ChatMessage";

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  code?: string;
  execution_result?: string;
  filePath?: string;
  fileName?: string;
}

interface ChatInterfaceProps {
  initialMessages?: Message[];
  sessionId: string;
}

export default function ChatInterface({ initialMessages = [], sessionId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // 自动滚动到最新消息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 从本地存储加载当前会话消息历史
  useEffect(() => {
    if (!sessionId) return;
    const savedMessages = localStorage.getItem(`chatMessages:${sessionId}`);
    if (savedMessages) {
      try {
        const parsedMessages = JSON.parse(savedMessages, (key, value) => {
          if (key === 'timestamp') {
            return new Date(value);
          }
          return value;
        });
        setMessages(parsedMessages);
      } catch (error) {
        console.error('Failed to parse saved messages:', error);
        setMessages([]);
      }
    } else {
      setMessages([]);
    }
  }, [sessionId]);

  // 保存当前会话消息到本地存储
  useEffect(() => {
    if (!sessionId) return;
    localStorage.setItem(`chatMessages:${sessionId}`, JSON.stringify(messages));
  }, [messages, sessionId]);

  // 不再提供清空所有消息按钮（由侧边栏删除会话完成）

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() && !file) return;
    
    // 添加用户消息
    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
      fileName: file?.name, // 保存文件名
      filePath: file ? URL.createObjectURL(file) : undefined
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append("instruction", input);
      
      // 添加消息历史记录到请求中
      // 只发送最近的10条消息，避免请求过大
      // 确保包含当前用户刚刚输入的消息
      const allMessages = [...messages, userMessage];
      const recentMessages = allMessages.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.content,
        fileName: msg.fileName,
        filePath: msg.filePath,
        code: msg.code,
        execution_result: msg.execution_result
      }));
      formData.append("messages_json", JSON.stringify(recentMessages));
      
      if (file) {
        formData.append("file", file);
        setFile(null);
      }
      
      const response = await fetch("/api/process", {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "请求处理失败");
      }
      
      const result = await response.json();
      
      // 添加AI回复消息
      const assistantMessage: Message = {
        role: 'assistant',
        content: result.response,
        timestamp: new Date(),
        code: result.code,
        execution_result: result.execution_result,
        filePath: result.filePath // 保存文件路径
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      // 添加错误消息
      const errorMessage: Message = {
        role: 'assistant',
        content: `处理请求时出错: ${err.message || "未知错误"}`,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[80vh] bg-white dark:bg-gray-800 rounded-lg shadow-md">
      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-400">
            <p>开始与AI助手对话吧！</p>
          </div>
        ) : (
          <>
            {/* 清空按钮已移除，使用侧边栏删除会话 */}
            {messages.map((msg, index) => (
              <ChatMessage key={index} message={msg} />
            ))}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {/* 输入区域 */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center mb-2">
          <label htmlFor="file-upload" className="cursor-pointer">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-500 hover:text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
            <input
              id="file-upload"
              type="file"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </label>
          {file && (
            <span className="ml-2 text-sm text-gray-600 dark:text-gray-300 flex items-center">
              {file.name}
              <button 
                type="button" 
                className="ml-1 text-red-500"
                onClick={() => setFile(null)}
              >
                ×
              </button>
            </span>
          )}
        </div>
        
        <div className="flex">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            className={`px-4 py-2 rounded-r-md text-white ${
              loading ? "bg-blue-400" : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? (
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              "发送"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}