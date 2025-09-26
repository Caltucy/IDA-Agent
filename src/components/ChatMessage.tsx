"use client";

import { useState } from "react";
import { ChatMessage as ChatMessageType, StreamingStep } from "../types";

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const [showThoughts, setShowThoughts] = useState(false);
  const [showStreamingSteps, setShowStreamingSteps] = useState(true);
  const isUser = message.role === 'user';
  const date = message.timestamp instanceof Date ? message.timestamp : new Date(message.timestamp);
  
  const renderStreamingStep = (step: StreamingStep, index: number) => {
    const stepNumber = step.step;
    
    return (
      <div key={index} className="mb-3 p-3 bg-gray-50 dark:bg-gray-800 rounded border-l-4 border-blue-500">
        <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
          步骤 {stepNumber}
        </div>
        
        {step.type === 'step_start' && (
          <div className="text-sm text-blue-600 dark:text-blue-400 mb-2">
            🤔 {step.message}
          </div>
        )}
        
        {step.type === 'thought' && step.content && (
          <div className="mb-2">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">💭 思考:</div>
            <div className="text-sm text-gray-800 dark:text-gray-200 bg-blue-50 dark:bg-blue-900/20 p-2 rounded">
              {step.content}
            </div>
          </div>
        )}
        
        {step.type === 'action' && step.action && (
          <div className="mb-2">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">⚡ 行动:</div>
            <div className="text-sm text-gray-800 dark:text-gray-200 bg-green-50 dark:bg-green-900/20 p-2 rounded">
              {step.action}
              {step.action_input && Object.keys(step.action_input).length > 0 && (
                <div className="mt-1 text-xs">
                  <strong>输入:</strong> {JSON.stringify(step.action_input, null, 2)}
                </div>
              )}
            </div>
          </div>
        )}
        
        {step.type === 'code_execution_start' && step.code && (
          <div className="mb-2">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">💻 执行代码:</div>
            <div className="text-sm bg-gray-800 text-gray-100 p-2 rounded overflow-x-auto">
              <pre><code>{step.code}</code></pre>
            </div>
          </div>
        )}
        
        {step.type === 'code_execution_result' && step.result && (
          <div className="mb-2">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">📊 执行结果:</div>
            <div className="text-sm text-gray-800 dark:text-gray-200 bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded">
              <pre className="whitespace-pre-wrap">{step.result}</pre>
            </div>
          </div>
        )}
        
        {step.type === 'observation' && step.content && (
          <div className="mb-2">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">👁️ 观察:</div>
            <div className="text-sm text-gray-800 dark:text-gray-200 bg-purple-50 dark:bg-purple-900/20 p-2 rounded">
              {step.content}
            </div>
          </div>
        )}
        
        {step.type === 'final_answer' && step.content && (
          <div className="mb-2">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">✅ 最终答案:</div>
            <div className="text-sm text-gray-800 dark:text-gray-200 bg-green-50 dark:bg-green-900/20 p-2 rounded">
              {step.content}
            </div>
          </div>
        )}
        
        {step.type === 'error' && step.message && (
          <div className="mb-2">
            <div className="text-xs font-medium text-red-600 dark:text-red-400 mb-1">❌ 错误:</div>
            <div className="text-sm text-red-800 dark:text-red-200 bg-red-50 dark:bg-red-900/20 p-2 rounded">
              {step.message}
            </div>
          </div>
        )}
      </div>
    );
  };
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div 
        className={`max-w-[80%] rounded-lg p-4 ${
          isUser 
            ? 'bg-blue-500 text-white rounded-br-none' 
            : 'bg-gray-200 dark:bg-gray-700 rounded-bl-none'
        }`}
      >
        <div className="flex items-center mb-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-2 ${
            isUser 
              ? 'bg-blue-600' 
              : 'bg-purple-600 text-white'
          }`}>
            {isUser ? '你' : 'AI'}
          </div>
          <span className="text-sm opacity-75">
            {isNaN(date.getTime()) ? '' : date.toLocaleTimeString()}
          </span>
          {message.isStreaming && (
            <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
              实时思考中...
            </span>
          )}
        </div>
        
        <div className="whitespace-pre-wrap">{message.content}</div>
        
        {/* 流式思考步骤 */}
        {!isUser && message.streamingSteps && message.streamingSteps.length > 0 && (
          <div className="mt-3">
            <button
              onClick={() => setShowStreamingSteps(!showStreamingSteps)}
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center"
            >
              <svg 
                className={`w-4 h-4 mr-1 transition-transform ${showStreamingSteps ? 'rotate-90' : ''}`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              {showStreamingSteps ? '隐藏' : '显示'} 实时思考过程 ({message.streamingSteps.length} 步)
            </button>
            
            {showStreamingSteps && (
              <div className="mt-2 space-y-2">
                {message.streamingSteps.map((step, index) => 
                  renderStreamingStep(step, index)
                )}
              </div>
            )}
          </div>
        )}
        
        {/* 传统思考过程（兼容旧数据） */}
        {!isUser && message.thoughtSteps && message.thoughtSteps.length > 0 && (
          <div className="mt-3">
            <button
              onClick={() => setShowThoughts(!showThoughts)}
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center"
            >
              <svg 
                className={`w-4 h-4 mr-1 transition-transform ${showThoughts ? 'rotate-90' : ''}`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              {showThoughts ? '隐藏' : '显示'} AI思考过程 ({message.thoughtSteps.length} 步)
            </button>
            
            {showThoughts && (
              <div className="mt-2 space-y-3">
                {message.thoughtSteps.map((step, index) => (
                  <div key={index} className="bg-gray-50 dark:bg-gray-800 p-3 rounded border-l-4 border-blue-500">
                    <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      步骤 {index + 1}
                    </div>
                    
                    {step.thought && (
                      <div className="mb-2">
                        <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">思考:</div>
                        <div className="text-sm text-gray-800 dark:text-gray-200 bg-blue-50 dark:bg-blue-900/20 p-2 rounded">
                          {step.thought}
                        </div>
                      </div>
                    )}
                    
                    {step.action && (
                      <div className="mb-2">
                        <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">行动:</div>
                        <div className="text-sm text-gray-800 dark:text-gray-200 bg-green-50 dark:bg-green-900/20 p-2 rounded">
                          {step.action}
                        </div>
                      </div>
                    )}
                    
                    {step.action_input && Object.keys(step.action_input).length > 0 && (
                      <div className="mb-2">
                        <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">行动输入:</div>
                        <div className="text-sm text-gray-800 dark:text-gray-200 bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded">
                          <pre className="whitespace-pre-wrap text-xs">
                            {JSON.stringify(step.action_input, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                    
                    {step.observation && (
                      <div>
                        <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">观察:</div>
                        <div className="text-sm text-gray-800 dark:text-gray-200 bg-purple-50 dark:bg-purple-900/20 p-2 rounded">
                          {step.observation}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {message.code && (
          <div className="mt-3 bg-gray-800 text-gray-100 p-3 rounded overflow-x-auto">
            <pre><code>{message.code}</code></pre>
          </div>
        )}
        
        {message.execution_result && (
          <div className="mt-3 bg-gray-100 dark:bg-gray-800 p-3 rounded">
            <h4 className="text-sm font-semibold mb-1">执行结果:</h4>
            <pre className="whitespace-pre-wrap text-sm">{message.execution_result}</pre>
          </div>
        )}
      </div>
    </div>
  );
}