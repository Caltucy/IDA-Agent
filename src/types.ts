// 聊天消息类型
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  code?: string;
  execution_result?: string;
  filePath?: string;  // 添加文件路径字段
  fileName?: string;  // 添加文件名字段
}

// API响应类型
export interface ApiResponse {
  response: string;
  code?: string;
  execution_result?: string;
  filePath?: string;  // 添加文件路径字段
}