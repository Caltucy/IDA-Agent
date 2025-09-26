"use client";

import { useState, useRef, useEffect } from "react";
import ChatMessage from "./ChatMessage";
import { storageQueue } from "../lib/storageQueue";
import { ChatMessage as ChatMessageType, StreamingStep } from "../types";

interface ThoughtStep {
  thought: string;
  action: string;
  action_input: any;
  observation: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  code?: string;
  execution_result?: string;
  filePath?: string;
  fileName?: string;
  thoughtSteps?: ThoughtStep[];
}

interface ChatInterfaceProps {
  initialMessages?: Message[];
  sessionId: string;
}

export default function ChatInterface({ initialMessages = [], sessionId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessageType[]>(initialMessages);
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true); // 默认启用流式处理
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasLoadedRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);
  const retriedRef = useRef(false);
  
  // 自动滚动到最新消息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 从本地存储加载当前会话消息历史（含一次性重试）
  useEffect(() => {
    if (!sessionId) return;
    // 每次切换会话重置重试标记和加载标记
    retriedRef.current = false;
    hasLoadedRef.current = false;
    
    console.log(`[ChatInterface] 开始加载会话消息, sessionId: ${sessionId}`);
    
    const loadOnce = () => {
      try {
        // 使用队列机制获取消息，确保读取到最新数据
        const saved = storageQueue.getItem(`chatMessages:${sessionId}`);
        if (saved) {
          // 由于storageQueue.getItem已经解析了JSON，这里直接处理
          if (Array.isArray(saved)) {
            console.log(`[ChatInterface] 成功加载会话消息, 消息数量: ${saved.length}`);
            // 确保timestamp是Date对象
            const messagesWithDateObjects = saved.map(msg => ({
              ...msg,
              timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp)
            }));
            setMessages(messagesWithDateObjects);
            // 标记已完成首次加载，避免保存空数组覆盖历史
            hasLoadedRef.current = true;
            return true;
          }
        } else {
          // 新会话或无历史：清空UI中的旧消息
          console.log(`[ChatInterface] 无历史消息或新会话, sessionId: ${sessionId}`);
          setMessages([]);
          // 对于新会话，也标记为已加载
          hasLoadedRef.current = true;
          return false;
        }
      } catch (error) {
        console.error('[ChatInterface] 解析消息失败:', error);
      }
      return false;
    };

    // 首次加载尝试
    const loadSuccess = loadOnce();
    
    // 若首次读到为空或失败，进行一次轻量重试（可能由于其他组件仍在写入）
    if (!loadSuccess && !retriedRef.current) {
      retriedRef.current = true;
      setTimeout(() => {
        if (!sessionId) return;
        console.log(`[ChatInterface] 重试加载会话消息, sessionId: ${sessionId}`);
        try {
          // 使用队列机制获取消息，确保读取到最新数据
          const savedRetry = storageQueue.getItem(`chatMessages:${sessionId}`);
          if (savedRetry) {
            if (Array.isArray(savedRetry) && savedRetry.length > 0) {
              console.log(`[ChatInterface] 重试成功, 找到消息数量: ${savedRetry.length}`);
              // 确保timestamp是Date对象
              const messagesWithDateObjects = savedRetry.map(msg => ({
                ...msg,
                timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp)
              }));
              setMessages(messagesWithDateObjects);
              hasLoadedRef.current = true;
            } else {
              console.log(`[ChatInterface] 重试结果为空或非数组`);
            }
          } else {
            console.log(`[ChatInterface] 重试加载无结果`);
          }
        } catch (err) {
          console.error('[ChatInterface] 重试解析消息失败:', err);
        }
      }, 500); // 增加延迟时间，确保队列有足够时间处理
    }
  }, [sessionId]);

  // 监听 storage 事件（跨标签或其他组件更新时刷新当前会话消息）
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (!sessionId) return;
      if (e.key === `chatMessages:${sessionId}` && e.newValue) {
        try {
          console.log(`[ChatInterface] 检测到storage事件更新, sessionId: ${sessionId}`);
          const parsed = JSON.parse(e.newValue, (key, value) => (key === 'timestamp' ? new Date(value) : value));
          if (Array.isArray(parsed)) {
            // 确保不会覆盖当前正在编辑的消息
            setMessages(currentMessages => {
              // 如果当前消息数量大于等于新消息数量，保留当前消息
              if (currentMessages.length >= parsed.length) {
                console.log(`[ChatInterface] 保留当前消息(${currentMessages.length})，不覆盖为storage事件消息(${parsed.length})`);
                return currentMessages;
              }
              console.log(`[ChatInterface] 更新为storage事件消息, 消息数量: ${parsed.length}`);
              return parsed;
            });
          }
        } catch (err) {
          console.error('[ChatInterface] 处理storage事件失败:', err);
        }
      }
    };
    window.addEventListener('storage', handler);
    return () => window.removeEventListener('storage', handler);
  }, [sessionId]);

  // 保存当前会话消息到本地存储
  useEffect(() => {
    if (!sessionId) return;
    // 避免在首次挂载、尚未加载历史时把空数组写回覆盖历史
    if (!hasLoadedRef.current) return;
    
    // 添加条件：只有当消息数组不为空或者用户主动清空时才保存
    // 这样可以避免在会话切换时自动保存空数组覆盖历史消息
    const shouldSave = messages.length > 0 || (messages.length === 0 && document.activeElement?.id === 'clear-button');
    
    if (!shouldSave) {
      console.log(`[ChatInterface] 跳过保存空消息数组, sessionId: ${sessionId}`);
      return;
    }

    console.log(`[ChatInterface] 保存消息到本地存储, sessionId: ${sessionId}, 消息数量: ${messages.length}`);
    
    // 使用队列机制保存消息，避免并发问题
    storageQueue.enqueue(`chatMessages:${sessionId}`, messages)
      .then(success => {
        console.log(`[ChatInterface] 保存消息${success ? '成功' : '失败'}, sessionId: ${sessionId}`);
      })
      .catch(err => console.error('[ChatInterface] 保存消息失败:', err));

    // 同步更新侧边栏会话的更新时间
    try {
      // 使用队列机制获取最新会话列表
      const sessions = storageQueue.getItem('chatSessions');
      if (sessions && Array.isArray(sessions)) {
        console.log(`[ChatInterface] 更新会话时间戳, sessionId: ${sessionId}`);
        const now = Date.now();
        const updated = sessions.map(s => s.id === sessionId ? { ...s, updatedAt: now } : s);
        // 使用队列机制保存会话列表
        storageQueue.enqueue('chatSessions', updated)
          .then(success => {
            console.log(`[ChatInterface] 更新会话时间戳${success ? '成功' : '失败'}`);
          })
          .catch(err => console.error('[ChatInterface] 更新会话时间戳失败:', err));
      }
    } catch (err) {
      console.error('[ChatInterface] 处理会话列表失败:', err);
    }
  }, [messages, sessionId]);

  // 切换会话时中止未完成请求并复位 loading
  useEffect(() => {
    // 不再中止请求，允许其在后台继续执行，仅重置本会话的 loading 展示
    setLoading(false);
  }, [sessionId]);

  // 不再提供清空所有消息按钮（由侧边栏删除会话完成）

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() && !file) return;
    
    const targetSessionId = sessionId; // 绑定此次请求的会话ID

    // 添加用户消息
    const userMessage: ChatMessageType = {
      role: 'user',
      content: input,
      timestamp: new Date(),
      fileName: file?.name,
      filePath: file ? URL.createObjectURL(file) : undefined
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append("instruction", input);
      formData.append("use_stream", useStreaming.toString());
      
      // 添加消息历史记录到请求中
      const allMessages = [...messages, userMessage];
      const recentMessages = allMessages.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.content,
        fileName: msg.fileName,
        filePath: msg.filePath,
        code: msg.code,
        execution_result: msg.execution_result,
        thoughtSteps: msg.thoughtSteps
      }));
      formData.append("messages_json", JSON.stringify(recentMessages));
      
      if (file) {
        formData.append("file", file);
        setFile(null);
      }
      
      // 为此次请求创建可中止控制器
      if (abortRef.current) {
        try { abortRef.current.abort(); } catch {}
      }
      const controller = new AbortController();
      abortRef.current = controller;

      if (useStreaming) {
        // 流式处理
        const response = await fetch("/api/process", {
          method: "POST",
          body: formData,
          signal: controller.signal,
        });
        
        if (!response.ok) {
          throw new Error("请求处理失败");
        }

        // 创建流式消息
        const streamingMessage: ChatMessageType = {
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          isStreaming: true,
          streamingSteps: []
        };

        // 立即添加到消息列表
        setMessages(prev => [...prev, streamingMessage]);

        // 处理流式数据
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') {
                  // 流结束
                  setMessages(prev => prev.map((msg, index) => 
                    index === prev.length - 1 && msg.isStreaming 
                      ? { ...msg, isStreaming: false }
                      : msg
                  ));
                  break;
                }

                try {
                  const stepData: StreamingStep = JSON.parse(data);
                  
                  // 更新流式消息
                  setMessages(prev => prev.map((msg, index) => {
                    if (index === prev.length - 1 && msg.isStreaming) {
                      const updatedSteps = [...(msg.streamingSteps || []), stepData];
                      
                      // 根据步骤类型更新消息内容
                      let updatedContent = msg.content;
                      if (stepData.type === 'final_answer' || stepData.type === 'final_response') {
                        updatedContent = stepData.content || '';
                      }

                      return {
                        ...msg,
                        content: updatedContent,
                        streamingSteps: updatedSteps,
                        code: stepData.code || msg.code,
                        execution_result: stepData.result || msg.execution_result
                      };
                    }
                    return msg;
                  }));
                } catch (e) {
                  console.error('解析流式数据失败:', e);
                }
              }
            }
          }
        }
      } else {
        // 非流式处理（原有逻辑）
        const response = await fetch("/api/process", {
          method: "POST",
          body: formData,
          signal: controller.signal,
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "请求处理失败");
        }
        
        const result = await response.json();
        
        const assistantMessage: ChatMessageType = {
          role: 'assistant',
          content: result.response,
          timestamp: new Date(),
          code: result.code,
          execution_result: result.execution_result,
          filePath: result.filePath,
          thoughtSteps: result.intermediate_steps
        };
        
        if (sessionId === targetSessionId) {
          setMessages(prev => [...prev, assistantMessage]);
        }
      }
    } catch (err: any) {
      if (err?.name === 'AbortError') {
        return;
      }
      const errorMessage: ChatMessageType = {
        role: 'assistant',
        content: `处理请求时出错: ${err.message || "未知错误"}`,
        timestamp: new Date()
      };
      if (sessionId === targetSessionId) {
        setMessages(prev => [...prev, errorMessage]);
      }
      console.error("Error:", err);
    } finally {
      if (sessionId === targetSessionId) {
        setLoading(false);
      }
      if (abortRef.current) {
        abortRef.current = null;
      }
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
          
          {/* 流式处理开关 */}
          <div className="ml-auto flex items-center">
            <label className="text-sm text-gray-600 dark:text-gray-300 mr-2">
              实时显示思考过程
            </label>
            <input
              type="checkbox"
              checked={useStreaming}
              onChange={(e) => setUseStreaming(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
          </div>
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