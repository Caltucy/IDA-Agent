'use client';

import { useState, useEffect } from 'react';

export default function FilesPage() {
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string[] | null>(null);

  const fetchFiles = async () => {
    const res = await fetch('/api/files');
    const data = await res.json();
    setFiles(data);
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    await fetch('/api/files', {
      method: 'POST',
      body: formData,
    });

    fetchFiles();
  };

  const handlePreview = async (filename: string) => {
    const res = await fetch(`/api/files/${filename}`);
    const data = await res.json();
    setPreview(data);
  };

  const handleDelete = async (filename: string) => {
    await fetch(`/api/files/${filename}`, {
      method: 'DELETE',
    });

    fetchFiles();
    setPreview(null);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">文件管理</h1>

      <div className="mb-4">
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} className="bg-blue-500 text-white px-4 py-2 rounded ml-2">上传文件</button>
      </div>

      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-2">文件列表</h2>
        <ul>
          {files.map((file) => (
            <li key={file} className="flex justify-between items-center p-2 border-b">
              <span>{file}</span>
              <div>
                <button onClick={() => handlePreview(file)} className="bg-green-500 text-white px-2 py-1 rounded mr-2">预览</button>
                <button onClick={() => handleDelete(file)} className="bg-red-500 text-white px-2 py-1 rounded">删除</button>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {preview && (
        <div>
          <h2 className="text-xl font-semibold mb-2">文件预览 (前10行)</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border">
              <thead>
                <tr>
                  {preview[0].split(',').map((header, index) => (
                    <th key={index} className="py-2 px-4 border-b bg-gray-100">{header}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.slice(1).map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {row.split(',').map((cell, cellIndex) => (
                      <td key={cellIndex} className="py-2 px-4 border-b text-center">{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}