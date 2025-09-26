"use client";

import { useEffect, useRef, useState } from "react";
import { AnalysisResponse, ChatMessage } from "../types";
import StepDisplay from "./StepDisplay";
import ChartRenderer from "./ChartRenderer";
import MatlabChartRenderer from "./MatlabChartRenderer";

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const raw = localStorage.getItem("ida_chat_history");
      return raw ? (JSON.parse(raw) as ChatMessage[]) : [];
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [showMatlabData, setShowMatlabData] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 保存消息到localStorage
  useEffect(() => {
    try {
      localStorage.setItem("ida_chat_history", JSON.stringify(messages));
    } catch (error) {
      console.error("保存聊天历史失败:", error);
    }
  }, [messages]);

  // 自动滚动到底部
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const onSend = async () => {
    const content = input.trim();
    if (!content && !file) return;
    
    const nextMessages = [...messages, { role: "user", content } as ChatMessage];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append("instruction", content || "");
      if (file) formData.append("file", file);
      
      // 传递最近10条消息作为历史
      const recent = nextMessages.slice(-10);
      formData.append("history", JSON.stringify(recent));

      const res = await fetch("/api/process", { method: "POST", body: formData });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "请求失败");
      }
      
      const data: AnalysisResponse & { charts?: any[]; execution_result?: string } = await res.json();

      // 添加文本回复
      const reportText = data.report || data.response || "";
      if (reportText && reportText.trim().length > 0) {
        setMessages((prev) => [...prev, { role: "assistant", content: reportText }]);
      }

      // 添加步骤展示
      if (data.intermediate_steps && data.intermediate_steps.length > 0) {
        setMessages((prev) => [
          ...prev,
          { 
            role: "assistant", 
            content: `__STEPS__${JSON.stringify(data.intermediate_steps)}` 
          }
        ]);
      }

      // 添加图表展示
      if (data.charts && data.charts.length > 0) {
        setMessages((prev) => [
          ...prev,
          { 
            role: "assistant", 
            content: `__CHARTS__${JSON.stringify(data.charts)}` 
          }
        ]);
      }

      // 兜底：如果没有文本报告但有执行结果
      if ((!reportText || reportText.trim().length === 0) && 
          typeof data.execution_result === "string" && 
          data.execution_result.trim().length > 0) {
        setMessages((prev) => [...prev, { role: "assistant", content: data.execution_result as string }]);
      }

    } catch (e: any) {
      setMessages((prev) => [...prev, { role: "assistant", content: `出错: ${e.message || e}` }]);
    } finally {
      setLoading(false);
      setFile(null);
    }
  };

  // 分析文件
  const analyzeFile = async () => {
    if (!file) return;
    
    const nextMessages = [...messages, { role: "user", content: "请分析我上传的文件" } as ChatMessage];
    setMessages(nextMessages);
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append("instruction", "");
      formData.append("file", file);
      
      const recent = nextMessages.slice(-10);
      formData.append("history", JSON.stringify(recent));
      
      const res = await fetch("/api/process", { method: "POST", body: formData });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "请求失败");
      }
      
      const data: AnalysisResponse & { charts?: any[]; execution_result?: string } = await res.json();
      
      // 添加文本回复 - 改进显示逻辑
      const reportText = data.report || data.response || data.final_answer || "";
      if (reportText && reportText.trim()) {
        setMessages((prev) => [...prev, { role: "assistant", content: reportText }]);
      } else {
        // 如果没有文本回复，显示执行结果
        const executionResult = data.execution_result || "";
        if (executionResult && executionResult.trim()) {
          setMessages((prev) => [...prev, { role: "assistant", content: `执行结果：\n${executionResult}` }]);
        } else {
          setMessages((prev) => [...prev, { role: "assistant", content: "文件分析完成，但未生成具体内容。" }]);
        }
      }

      // 添加步骤展示
      if (data.intermediate_steps && data.intermediate_steps.length > 0) {
        setMessages((prev) => [
          ...prev,
          { 
            role: "assistant", 
            content: `__STEPS__${JSON.stringify(data.intermediate_steps)}` 
          }
        ]);
      }

      // 添加图表展示
      if (data.charts && data.charts.length > 0) {
        setMessages((prev) => [
          ...prev,
          { 
            role: "assistant", 
            content: `__CHARTS__${JSON.stringify(data.charts)}` 
          }
        ]);
      }

      // 兜底
      if (!reportText && typeof data.execution_result === "string" && data.execution_result.trim()) {
        setMessages((prev) => [...prev, { role: "assistant", content: data.execution_result as string }]);
      }

    } catch (e: any) {
      setMessages((prev) => [...prev, { role: "assistant", content: `出错: ${e.message || e}` }]);
    } finally {
      setLoading(false);
    }
  };

  // 渲染消息内容
  const renderMessageContent = (content: string) => {
    if (content.startsWith("__STEPS__")) {
      try {
        const json = content.replace("__STEPS__", "");
        const steps = JSON.parse(json);
        console.log("渲染步骤:", steps); // 调试日志
        return <StepDisplay steps={steps} />;
      } catch (error) {
        console.error("步骤数据解析失败:", error);
        return <span className="text-red-500">步骤数据解析失败: {String(error)}</span>;
      }
    }
    
    if (content.startsWith("__CHARTS__")) {
      try {
        const json = content.replace("__CHARTS__", "");
        const charts = JSON.parse(json);
        console.log("渲染图表:", charts); // 调试日志
        return <ChartRenderer charts={charts} />;
      } catch (error) {
        console.error("图表数据解析失败:", error);
        return <span className="text-red-500">图表数据解析失败: {String(error)}</span>;
      }
    }
    
    if (content.startsWith("__MATLAB__")) {
      try {
        const json = content.replace("__MATLAB__", "");
        if (json.trim() === "") {
          // 如果没有JSON数据，直接渲染组件让它自动加载
          console.log("渲染MATLAB组件，自动加载数据");
          return <MatlabChartRenderer />;
        }
        const matlabData = JSON.parse(json);
        console.log("渲染MATLAB数据:", matlabData); // 调试日志
        return <MatlabChartRenderer data={matlabData} />;
      } catch (error) {
        console.error("MATLAB数据解析失败:", error);
        return <span className="text-red-500">MATLAB数据解析失败: {String(error)}</span>;
      }
    }
    
    return <div className="whitespace-pre-wrap">{content}</div>;
  };

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col">
      {/* 对话区域 */}
      <div className="flex-1 bg-gray-800 border border-gray-600 rounded-lg shadow-sm overflow-hidden">
        <div className="h-full overflow-y-auto p-4">
        {messages.length === 0 && (
            <div className="h-full flex items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="text-4xl mb-4">💬</div>
                <p className="text-lg mb-2">开始你的对话吧</p>
                <p className="text-sm">可以上传文件并提问，我会为你分析数据</p>
              </div>
            </div>
          )}
          
        <div className="space-y-4">
          {messages.map((m, idx) => (
            <div key={idx} className={m.role === "user" ? "text-right" : "text-left"}>
              {/* 显示对话双方名称 */}
              <div className={`text-xs font-medium mb-1 ${
                m.role === "user" ? "text-blue-400" : "text-green-400"
              }`}>
                {m.role === "user" ? "👤 用户" : "🤖 IDA助手"}
              </div>
              <div className={`inline-block px-4 py-3 rounded-lg max-w-[80%] ${
                m.role === "user" 
                  ? "bg-blue-600 text-white" 
                  : "bg-gray-700 text-gray-200"
              }`}>
                {renderMessageContent(m.content)}
              </div>
            </div>
          ))}
            
          {loading && (
            <div className="text-left">
              {/* 显示助手名称 */}
              <div className="text-xs font-medium mb-1 text-green-400">
                🤖 IDA助手
              </div>
              <div className="inline-block px-4 py-3 rounded-lg bg-gray-700 text-gray-300">
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-300 mr-2"></div>
                  正在思考...
                </div>
              </div>
            </div>
          )}
          <div ref={scrollRef} />
          </div>
        </div>
      </div>

      {/* 输入区域 */}
      <div className="mt-4 space-y-3">
        {/* MATLAB数据按钮 */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setShowMatlabData(!showMatlabData);
              if (!showMatlabData) {
                setMessages(prev => [...prev, { 
                  role: "assistant", 
                  content: "__MATLAB__" 
                }]);
              }
            }}
            className={`px-4 py-2 rounded-md text-white font-medium transition-colors ${
              showMatlabData 
                ? "bg-green-600 hover:bg-green-700" 
                : "bg-purple-600 hover:bg-purple-700"
            }`}
          >
            {showMatlabData ? "隐藏MATLAB数据" : "显示MATLAB数据"}
          </button>
        </div>

        {/* 文件上传区域 */}
        <div className="flex items-center gap-3">
        <input
          type="file"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="flex-1 text-sm px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-200"
            accept=".xlsx,.xls,.csv,.txt"
        />
        {file && (
          <button
            onClick={analyzeFile}
            disabled={loading}
              className={`px-4 py-2 rounded-md text-white font-medium transition-colors ${
              loading ? "bg-green-400" : "bg-green-600 hover:bg-green-700"
            }`}
          >
            {loading ? "分析中..." : "开始分析"}
          </button>
        )}
      </div>

        {/* 文本输入区域 */}
        <div className="flex gap-3">
        <textarea
            className="flex-1 px-4 py-3 border border-gray-600 rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-700 text-gray-200 placeholder-gray-400"
            placeholder="请输入你的问题..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
            rows={3}
            onKeyPress={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
        />
        <button
          onClick={onSend}
            disabled={loading || (!input.trim() && !file)}
            className={`px-6 py-3 rounded-md text-white font-medium transition-colors ${
              loading || (!input.trim() && !file)
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
        >
          发送
        </button>
        </div>
      </div>
    </div>
  );
}