"use client";

import { useState } from "react";
import FileUploadForm from "../components/FileUploadForm";
import ResponseDisplay from "../components/ResponseDisplay";

export default function Home() {
  const [response, setResponse] = useState(null);

  const handleResponse = (data: any) => {
    setResponse(data);
  };

  return (
    <div className="flex flex-col items-center min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-4 sm:p-8">
      <main className="w-full max-w-4xl mx-auto">
        <div className="flex justify-center items-center mb-8">
          <h1 className="text-4xl font-bold text-center">数据分析代理</h1>
        </div>

        <FileUploadForm onSubmit={handleResponse} />
        <ResponseDisplay response={response} />
      </main>
    </div>
  );
}
