export interface Chart {
  type: 'bar' | 'line';
  title?: string;
  data: {
    labels: string[];
    values: number[];
    seriesName?: string;
  };
}

export interface AnalysisStep {
  step_id?: string;
  thought?: string;
  action?: string;
  action_input?: any;
  observation?: string;
  code?: string;
  execution_result?: string;
  timestamp?: string;
  status?: 'pending' | 'running' | 'completed' | 'error';
}

export interface AnalysisResponse {
  response?: string;
  report?: string;
  final_answer?: string;
  charts?: Chart[];
  code?: string;
  execution_result?: string;
  intermediate_steps?: AnalysisStep[];
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}