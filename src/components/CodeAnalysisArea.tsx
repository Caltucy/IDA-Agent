"use client";

import { useState } from "react";
import { AnalysisStep } from "../types";
import StepDisplay from "./StepDisplay";
import ChartRenderer from "./ChartRenderer";

interface CodeAnalysisAreaProps {
  steps: AnalysisStep[];
  charts?: any[];
  isAnalyzing?: boolean;
  currentDocument?: any;
}

export default function CodeAnalysisArea({ 
  steps, 
  charts, 
  isAnalyzing = false, 
  currentDocument 
}: CodeAnalysisAreaProps) {
  const [activeTab, setActiveTab] = useState<"steps" | "charts" | "code">("steps");

  return (
    <div className="h-full flex flex-col bg-white border-l border-gray-200">
      {/* 标题栏 */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">代码分析</h2>
          {currentDocument && (
            <div className="text-sm text-gray-600">
              当前文档: <span className="font-medium">{currentDocument.name}</span>
            </div>
          )}
        </div>
      </div>

      {/* 标签页 */}
      <div className="flex border-b border-gray-200 bg-white">
        <button
          onClick={() => setActiveTab("steps")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "steps"
              ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50"
              : "text-gray-600 hover:text-gray-800 hover:bg-gray-50"
          }`}
        >
          分析步骤
        </button>
        <button
          onClick={() => setActiveTab("charts")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "charts"
              ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50"
              : "text-gray-600 hover:text-gray-800 hover:bg-gray-50"
          }`}
        >
          数据图表
        </button>
        <button
          onClick={() => setActiveTab("code")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "code"
              ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50"
              : "text-gray-600 hover:text-gray-800 hover:bg-gray-50"
          }`}
        >
          代码总览
        </button>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto p-4">
        {isAnalyzing && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              <span className="text-blue-800 text-sm">正在分析中...</span>
            </div>
          </div>
        )}

        {activeTab === "steps" && (
          <div>
            {steps && steps.length > 0 ? (
              <StepDisplay steps={steps} isStreaming={isAnalyzing} />
            ) : (
              <div className="text-center text-gray-500 py-8">
                <div className="text-4xl mb-2">🔍</div>
                <p>暂无分析步骤</p>
                <p className="text-sm">开始对话以查看分析过程</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "charts" && (
          <div>
            {charts && charts.length > 0 ? (
              <ChartRenderer charts={charts} />
            ) : (
              <div className="text-center text-gray-500 py-8">
                <div className="text-4xl mb-2">📊</div>
                <p>暂无图表数据</p>
                <p className="text-sm">分析完成后将显示可视化图表</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "code" && (
          <div>
            {steps && steps.length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">代码总览</h3>
                {steps
                  .filter(step => step.code)
                  .map((step, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                      <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                        <h4 className="font-medium text-gray-800">
                          步骤 {index + 1}: {step.action || "代码执行"}
                        </h4>
                        {step.thought && (
                          <p className="text-sm text-gray-600 mt-1">{step.thought}</p>
                        )}
                      </div>
                      <div className="p-4">
                        <pre className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-sm">
                          <code>{step.code}</code>
                        </pre>
                        {step.execution_result && (
                          <div className="mt-3 p-3 bg-gray-50 rounded-md">
                            <h5 className="text-sm font-medium text-gray-700 mb-2">执行结果:</h5>
                            <div className="text-sm text-gray-600 whitespace-pre-wrap">
                              {step.execution_result}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <div className="text-4xl mb-2">💻</div>
                <p>暂无代码</p>
                <p className="text-sm">分析完成后将显示所有执行代码</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}





