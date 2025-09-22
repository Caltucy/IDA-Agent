"use client";

import { useState } from "react";

interface FileUploadFormProps {
  onSubmit: (response: any) => void;
}

export default function FileUploadForm({ onSubmit }: FileUploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [instruction, setInstruction] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!instruction.trim()) {
      setError("请输入指令");
      return;
    }
    
    setLoading(true);
    setError("");
    
    try {
      const formData = new FormData();
      formData.append("instruction", instruction);
      
      if (file) {
        formData.append("file", file);
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
      onSubmit(result);
    } catch (err: any) {
      setError(err.message || "处理请求时出错");
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-6 text-center">数据分析助手</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="file" className="block text-sm font-medium mb-1">
            上传文件（可选）
          </label>
          <input
            type="file"
            id="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md"
          />
        </div>
        
        <div>
          <label htmlFor="instruction" className="block text-sm font-medium mb-1">
            输入指令
          </label>
          <textarea
            id="instruction"
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="请输入您的指令，例如：分析这个CSV文件并生成图表"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md h-32"
            required
          />
        </div>
        
        <button
          type="submit"
          disabled={loading}
          className={`w-full py-2 px-4 rounded-md text-white font-medium ${
            loading ? "bg-blue-400" : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loading ? "处理中..." : "提交"}
        </button>
      </form>
    </div>
  );
}