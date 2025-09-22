import { StateGraph, END } from '@langchain/langgraph';
import { ChatOpenAI } from '@langchain/openai';
import { ToolNode } from '@langchain/langgraph/prebuilt';
import { AIMessage, BaseMessage } from '@langchain/core/messages';
import { FileReaderTool } from '@/tools/fileReader';

// 1. Define the state
interface AgentState {
  messages: BaseMessage[];
  filename: string;
}

// 2. Define the tools
const tools = [new FileReaderTool()];
const toolNode = new ToolNode<AgentState>(tools);

// 3. Define the model
const model = new ChatOpenAI({
  temperature: 0,
  modelName: process.env.OPENAI_MODEL_NAME || 'gpt-4o-mini',
}).bindTools(tools);

// 4. Define the nodes
async function callModel(state: AgentState) {
  const { messages } = state;
  const response = await model.invoke(messages);
  return { messages: [response] };
}

// 5. Define the edges
function shouldContinue(state: AgentState): 'tools' | typeof END {
  const { messages } = state;
  const lastMessage = messages[messages.length - 1];
  if (lastMessage instanceof AIMessage && lastMessage.tool_calls && lastMessage.tool_calls.length > 0) {
    return 'tools';
  }
  return END;
}

// 6. Define the graph
const workflow = new StateGraph<AgentState>({ channels: { messages: { value: (x, y) => x.concat(y), default: () => [] }, filename: { value: (x, y) => y, default: () => '' } } })
  .addNode('agent', callModel)
  .addNode('tools', toolNode);

workflow.setEntryPoint('agent');
workflow.addConditionalEdges('agent', shouldContinue);
workflow.addEdge('tools', 'agent');

const app = workflow.compile();

export { app };