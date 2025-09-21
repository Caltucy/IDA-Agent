"use client";

import { useState } from "react";
import dynamic from 'next/dynamic';
import { Chart } from "../types";

const ChartRenderer = dynamic(() => import('../components/ChartRenderer'), { ssr: false });

export default function Home() {
  const [query, setQuery] = useState("");
  const [report, setReport] = useState("");
  const [charts, setCharts] = useState<Chart[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setReport("");
    setCharts([]);

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();
      setReport(data.report || "");
      setCharts(data.charts || []);
    } catch (error) {
      console.error("Error analyzing data:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-4 sm:p-8">
      <main className="w-full max-w-4xl mx-auto">
        <div className="flex justify-center items-center mb-8">
          <h1 className="text-4xl font-bold text-center">数据分析代理</h1>
          <a href="/files" className="ml-4 px-4 py-2 bg-green-600 text-white font-semibold rounded-lg shadow-md hover:bg-green-700">文件管理</a>
        </div>

        <form onSubmit={handleSubmit} className="mb-8">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full p-4 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700"
            rows={4}
            placeholder="请输入您的自然语言指令..."
          />
          <button
            type="submit"
            className="w-full mt-4 px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75 disabled:opacity-50"
            disabled={loading || !query}
          >
            {loading ? "分析中..." : "开始分析"}
          </button>
        </form>

        {loading && (
          <div className="text-center">
            <p>正在努力分析中，请稍候...</p>
          </div>
        )}

        {report && (
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mb-8">
            <h2 className="text-2xl font-bold mb-4">分析报告</h2>
            <p>{report}</p>
          </div>
        )}

        {charts.length > 0 && (
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-4">分析图表</h2>
            <ChartRenderer charts={charts} />
          </div>
        )}
      </main>
    </div>
  );
}
