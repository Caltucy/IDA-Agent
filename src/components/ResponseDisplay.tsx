"use client";

import ChartRenderer from "./ChartRenderer";
import { AnalysisResponse } from "../types";

interface ResponseDisplayProps {
  response: AnalysisResponse | null;
}

export default function ResponseDisplay({ response }: ResponseDisplayProps) {
  if (!response) {
    return null;
  }

  return (
    <div className="w-full max-w-6xl mx-auto mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">响应结果</h2>
      
      <div className="prose dark:prose-invert max-w-none">
        {/* 显示报告内容 */}
        <div className="mb-6">
          <h3 className="text-xl font-semibold mb-2">分析报告</h3>
          <div className="whitespace-pre-wrap bg-gray-50 dark:bg-gray-900 p-4 rounded-md">
            {response.report || response.response}
          </div>
        </div>

        {/* 显示图表 */}
        {response.charts && response.charts.length > 0 && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-4">数据可视化</h3>
            <ChartRenderer charts={response.charts} />
          </div>
        )}
        
        {response.code && (
          <div className="mb-4">
            <h3 className="text-xl font-semibold mb-2">生成的代码</h3>
            <pre className="bg-gray-50 dark:bg-gray-900 p-4 rounded-md overflow-x-auto">
              <code>{response.code}</code>
            </pre>
          </div>
        )}
        
        {response.execution_result && (
          <div>
            <h3 className="text-xl font-semibold mb-2">执行结果</h3>
            <div className="whitespace-pre-wrap bg-gray-50 dark:bg-gray-900 p-4 rounded-md">
              {response.execution_result}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}