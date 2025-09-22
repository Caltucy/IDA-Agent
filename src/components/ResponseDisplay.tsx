"use client";

interface ResponseDisplayProps {
  response: {
    response: string;
    code?: string;
    execution_result?: string;
  } | null;
}

export default function ResponseDisplay({ response }: ResponseDisplayProps) {
  if (!response) {
    return null;
  }

  return (
    <div className="w-full max-w-2xl mx-auto mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">响应结果</h2>
      
      <div className="prose dark:prose-invert max-w-none">
        <div className="mb-4">
          <h3 className="text-xl font-semibold mb-2">AI 回复</h3>
          <div className="whitespace-pre-wrap bg-gray-50 dark:bg-gray-900 p-4 rounded-md">
            {response.response}
          </div>
        </div>
        
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