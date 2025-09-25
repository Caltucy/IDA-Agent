"use client";

interface ChatMessageProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date | string | number;
    code?: string;
    execution_result?: string;
  };
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const date = message.timestamp instanceof Date ? message.timestamp : new Date(message.timestamp);
  
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
        </div>
        
        <div className="whitespace-pre-wrap">{message.content}</div>
        
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