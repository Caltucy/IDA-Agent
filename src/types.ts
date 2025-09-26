// 思考步骤类型
export interface ThoughtStep {
  thought: string;
  action: string;
  action_input: any;
  observation: string;
}

// 聊天消息类型
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  code?: string;
  execution_result?: string;
  filePath?: string;
  fileName?: string;
  thoughtSteps?: ThoughtStep[]; // 添加思考步骤
  isStreaming?: boolean; // 标识是否为流式消息
  streamingSteps?: StreamingStep[]; // 流式步骤数据
}

// 流式步骤类型
export interface StreamingStep {
  step: number;
  type: 'step_start' | 'thought' | 'action' | 'code_execution_start' | 'code_execution_result' | 'observation' | 'final_answer' | 'final_response' | 'error';
  content?: string;
  action?: string;
  action_input?: any;
  result?: string;
  code?: string;
  message?: string;
  intermediate_steps?: ThoughtStep[];
  execution_result?: string;
  file_path?: string;
}

// API响应类型
export interface ApiResponse {
  response: string;
  code?: string;
  execution_result?: string;
  filePath?: string;
  intermediate_steps?: ThoughtStep[]; // 添加思考步骤
}