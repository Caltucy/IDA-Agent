"use client";

import { useState, useEffect } from "react";

interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadTime: string;
  content?: string;
}

interface DocumentManagerProps {
  onDocumentSelect?: (document: Document) => void;
  selectedDocumentId?: string;
}

export default function DocumentManager({ onDocumentSelect, selectedDocumentId }: DocumentManagerProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [showUpload, setShowUpload] = useState(false);
  const [newDocumentName, setNewDocumentName] = useState("");

  // 从 localStorage 加载文档列表
  useEffect(() => {
    try {
      const saved = localStorage.getItem("ida_documents");
      if (saved) {
        setDocuments(JSON.parse(saved));
      }
    } catch (error) {
      console.error("加载文档列表失败:", error);
    }
  }, []);

  // 保存文档列表到 localStorage
  const saveDocuments = (docs: Document[]) => {
    try {
      localStorage.setItem("ida_documents", JSON.stringify(docs));
      setDocuments(docs);
    } catch (error) {
      console.error("保存文档列表失败:", error);
    }
  };

  // 添加新文档
  const addDocument = () => {
    if (!newDocumentName.trim()) return;
    
    const newDoc: Document = {
      id: Date.now().toString(),
      name: newDocumentName.trim(),
      type: "text",
      size: 0,
      uploadTime: new Date().toLocaleString(),
      content: ""
    };
    
    const updatedDocs = [...documents, newDoc];
    saveDocuments(updatedDocs);
    setNewDocumentName("");
    setShowUpload(false);
  };

  // 删除文档
  const deleteDocument = (id: string) => {
    if (confirm("确定要删除这个文档吗？")) {
      const updatedDocs = documents.filter(doc => doc.id !== id);
      saveDocuments(updatedDocs);
    }
  };

  // 选择文档
  const selectDocument = (document: Document) => {
    if (onDocumentSelect) {
      onDocumentSelect(document);
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="h-full flex flex-col bg-white border-r border-gray-200">
      {/* 标题栏 */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">文档管理</h2>
          <button
            onClick={() => setShowUpload(true)}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + 新建
          </button>
        </div>
      </div>

      {/* 新建文档输入框 */}
      {showUpload && (
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex gap-2">
            <input
              type="text"
              value={newDocumentName}
              onChange={(e) => setNewDocumentName(e.target.value)}
              placeholder="输入文档名称..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyPress={(e) => e.key === "Enter" && addDocument()}
            />
            <button
              onClick={addDocument}
              className="px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
            >
              创建
            </button>
            <button
              onClick={() => {
                setShowUpload(false);
                setNewDocumentName("");
              }}
              className="px-3 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors text-sm"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {/* 文档列表 */}
      <div className="flex-1 overflow-y-auto">
        {documents.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <div className="text-4xl mb-2">📄</div>
            <p>暂无文档</p>
            <p className="text-sm">点击"新建"创建第一个文档</p>
          </div>
        ) : (
          <div className="p-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className={`p-3 mb-2 rounded-lg border cursor-pointer transition-all ${
                  selectedDocumentId === doc.id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                }`}
                onClick={() => selectDocument(doc)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-800 truncate">{doc.name}</h3>
                    <div className="text-xs text-gray-500 mt-1">
                      <span className="inline-block mr-2">📄 {doc.type}</span>
                      <span className="inline-block mr-2">📏 {formatFileSize(doc.size)}</span>
                      <span className="inline-block">🕒 {doc.uploadTime}</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteDocument(doc.id);
                    }}
                    className="ml-2 p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                    title="删除文档"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 底部统计 */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-sm text-gray-600">
          共 {documents.length} 个文档
        </div>
      </div>
    </div>
  );
}





