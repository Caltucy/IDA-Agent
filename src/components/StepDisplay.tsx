"use client";

import { AnalysisStep } from "../types";
import { useState } from "react";

interface StepDisplayProps {
  steps: AnalysisStep[];
  isStreaming?: boolean;
}

// 安全的代码显示组件
const SafeCodeDisplay = ({ code, language = "python" }: { code: string; language?: string }) => {
  return (
    <div className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto">
      <div className="text-xs text-gray-400 mb-2 font-mono">
        {language.toUpperCase()}
      </div>
      <pre className="text-sm leading-relaxed whitespace-pre-wrap">
        <code>{code}</code>
      </pre>
    </div>
  );
};

export default function StepDisplay({ steps, isStreaming = false }: StepDisplayProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  const toggleStep = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'running':
        return '⏳';
      case 'error':
        return '❌';
      case 'pending':
        return '⏸️';
      default:
        return '📝';
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'running':
        return 'text-blue-600';
      case 'error':
        return 'text-red-600';
      case 'pending':
        return 'text-gray-600';
      default:
        return 'text-gray-600';
    }
  };

  if (!steps || steps.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 space-y-3">
      <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
        <span>分析步骤</span>
        {isStreaming && (
          <span className="text-sm text-blue-500 animate-pulse">正在执行...</span>
        )}
      </h4>
      
      <div className="space-y-2">
        {steps.map((step, index) => {
          const stepId = step.step_id || `step-${index}`;
          const isExpanded = expandedSteps.has(stepId);
          const hasContent = step.thought || step.code || step.execution_result || step.observation;
          
          return (
            <div
              key={stepId}
              className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
            >
              {/* 步骤头部 */}
              <div
                className="bg-gray-50 dark:bg-gray-800 px-4 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                onClick={() => hasContent && toggleStep(stepId)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      步骤 {index + 1}
                    </span>
                    <span className={getStatusColor(step.status)}>
                      {getStatusIcon(step.status)}
                    </span>
                    {step.action && (
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                        {step.action}
                      </span>
                    )}
                  </div>
                  {hasContent && (
                    <span className="text-gray-400 text-sm">
                      {isExpanded ? '▼' : '▶'}
                    </span>
                  )}
                </div>
              </div>

              {/* 步骤内容 */}
              {isExpanded && hasContent && (
                <div className="px-4 py-3 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
                  <div className="space-y-3">
                    {/* 思考过程 */}
                    {step.thought && (
                      <div>
                        <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          💭 思考过程
                        </h5>
                        <div className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-3 rounded-md">
                          {step.thought}
                        </div>
                      </div>
                    )}

                    {/* 代码 */}
                    {step.code && (
                      <div>
                        <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          💻 执行代码
                        </h5>
                        <SafeCodeDisplay code={step.code} language="python" />
                      </div>
                    )}

                    {/* 执行结果 */}
                    {step.execution_result && (
                      <div>
                        <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          📊 执行结果
                        </h5>
                        <div className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-3 rounded-md whitespace-pre-wrap">
                          {step.execution_result}
                        </div>
                      </div>
                    )}

                    {/* 观察结果 */}
                    {step.observation && (
                      <div>
                        <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          👁️ 观察结果
                        </h5>
                        <div className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-3 rounded-md">
                          {step.observation}
                        </div>
                      </div>
                    )}

                    {/* 时间戳 */}
                    {step.timestamp && (
                      <div className="text-xs text-gray-500 dark:text-gray-500">
                        执行时间: {new Date(step.timestamp).toLocaleString()}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
