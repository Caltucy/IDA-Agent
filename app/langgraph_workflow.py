from typing import Dict, TypedDict, Annotated, Sequence, List, Optional, Literal, Union, Any
import os, sys, json, logging, tempfile, shutil, subprocess, time, re, ast, contextlib, io, builtins
from langgraph.prebuilt import ToolNode
from langgraph_codeact import create_codeact
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
import os
import sys
import tempfile
import shutil
import subprocess
import logging
import json
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 定义状态类型
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "消息历史"]
    file_path: Optional[str]
    file_content: Optional[str]
    file_type: Optional[str]
    code_to_execute: Optional[str]
    execution_result: Optional[str]
    intermediate_steps: List[Dict[str, Any]]
    current_step: int
    max_iterations: int
    action: Optional[str]
    action_input: Optional[Union[Dict[str, Any], str]]
    observation: Optional[str]
    is_done: bool

# 初始化LLM
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"), temperature=0)

# 定义工具函数
def read_file_content(
    file_path: str,
    max_preview_lines: int = 10,
    max_preview_chars: int = 4000,
) -> str:
    """Read file content preview: binary files report length, text files return truncated preview."""
    binary_exts = {'.xlsx', '.xls', '.xlsb', '.xlsm', '.parquet', '.feather'}
    try:
        ext = os.path.splitext(file_path)[1].lower()
    except Exception:
        ext = ''

    if ext in binary_exts:
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            logger.info(f"Read binary file: {file_path}")
            return f"[binary file, length: {len(data)} bytes]"
        except Exception as e:
            logger.error(f"Failed to read binary file: {e}")
            return f"Failed to read file: {e}"

    encodings = ['utf-8', 'gbk', 'cp936', 'gb18030', 'latin1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content_parts: List[str] = []
                total_chars = 0
                line_count = 0
                line_limit_reached = False
                char_limit_reached = False

                while True:
                    line = file.readline()
                    if line == '':
                        break

                    content_parts.append(line)
                    total_chars += len(line)
                    line_count += 1

                    if total_chars >= max_preview_chars:
                        char_limit_reached = True
                        break
                    if line_count >= max_preview_lines:
                        line_limit_reached = True
                        break

                truncated = False
                if char_limit_reached:
                    truncated = True
                elif line_limit_reached:
                    extra = file.read(1)
                    if extra:
                        truncated = True

                preview = ''.join(content_parts)
                if len(preview) > max_preview_chars:
                    preview = preview[:max_preview_chars]
                    truncated = True

                if truncated:
                    preview = preview[:max_preview_chars].rstrip('\n')
                    preview += f"\n... (preview truncated to {line_count} lines and approximately {len(preview)} characters)"

                logger.info(
                    f"Loaded preview with encoding {encoding}: {file_path} (lines: {line_count}, chars: {len(preview)})"
                )
                return preview
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            return f"Failed to read file: {e}"

    # If all encodings fail, fall back to binary read
    try:
        with open(file_path, 'rb') as file:
            binary_content = file.read()
        logger.warning(f"Fallback to binary read: {file_path}")
        return f"[binary file, length: {len(binary_content)} bytes]"
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        return f"Failed to read file: {e}"

def detect_file_type(file_path):
    """检测文件类型"""
    if file_path:
        extension = os.path.splitext(file_path)[1].lower()
        if extension in ['.csv', '.xlsx', '.xls']:
            return 'data'
        elif extension in ['.py']:
            return 'python'
        elif extension in ['.js', '.ts']:
            return 'javascript'
        elif extension in ['.json']:
            return 'json'
        elif extension in ['.txt', '.md']:
            return 'text'
    return 'unknown'

# ReAct Agent 核心逻辑
def react_agent_node(state: AgentState) -> AgentState:
    """ReAct Agent 的思考-行动循环"""
    # 如果已经完成或达到最大迭代次数，直接返回
    if state.get("is_done", False) or state.get("current_step", 0) >= state.get("max_iterations", 5):
        state["is_done"] = True
        
        # 确保生成最终回复
        if not any(isinstance(msg, AIMessage) for msg in state["messages"]):
            ai_message = AIMessage(content=f"已达到最大迭代次数 {state.get('max_iterations', 5)}，无法继续处理。请检查您的请求或尝试简化任务。")
            messages = list(state["messages"])
            messages.append(ai_message)
            state["messages"] = messages
            
        return state
    
    # 构建提示
    messages = list(state["messages"])
    
    # 添加文件信息（如果有）
    file_info = ""
    if state.get("file_path"):
        file_path = state["file_path"]
        file_type = state.get("file_type") or detect_file_type(file_path)
        file_content = state.get("file_content")
        
        if not file_content and os.path.exists(file_path):
            file_content = read_file_content(file_path)
            state["file_content"] = file_content
            state["file_type"] = file_type
        
        if file_content:
            file_info = f"文件路径: {file_path}\n文件类型: {file_type}\n文件内容:\n{file_content}\n"
    
    # 添加中间步骤历史
    steps_history = ""
    if state.get("intermediate_steps"):
        for i, step in enumerate(state["intermediate_steps"]):
            thought = step.get("thought", "")
            action = step.get("action", "")
            action_input = step.get("action_input")
            observation = step.get("observation", "")

            if isinstance(action_input, dict):
                action_input_str = json.dumps(action_input, ensure_ascii=False)
            elif action_input is None:
                action_input_str = ""
            else:
                action_input_str = str(action_input)

            steps_history += f"步骤 {i+1}:\n思考: {thought}\n行动: {action}\n行动输入: {action_input_str}\n观察: {observation}\n\n"
    
    # 构建系统提示
    system_prompt = f"""你是一个数据分析助手，使用ReAct（思考-行动）方法解决问题。
你可以进行如下行动，但每次只可选其一:
1. execute_code: 执行生成的代码并获取结果
2. final_answer: 生成最终回复内容并结束对话

{file_info if file_info else ""}

{steps_history if steps_history else ""}

你必须严格按照以下JSON格式进行回应：
'''
{{
  "thought": "在这里分析问题，制定计划，并反思。",
  "action": {{
    "name": "行动名称（execute_code 或 final_answer）",
    "input": "仅当行动名称为 'execute_code' 时，在此处生成要执行的Python代码；仅当行动名称为 'final_answer' 时，当你有足够信息回答用户问题时，在此处提供最终的文字答案。"
  }}
}}
'''
请注意：
- `action.input` 对象中，必须根据 `action.name` 的值提供代码或者回复内容。
- 你的整个输出必须是一个可以被 `json.loads()` 解析的、单一的、合法的JSON对象。

\n代码生成要求:
- 使用 pandas/numpy 等库处理数据时，务必使用 print 打印关键结果。
- 打印表格/序列前，设置完整显示选项: 
  - DataFrame/Series 请优先使用 to_string() 打印完整内容。
  - numpy 如需打印数组，可设置 threshold/edgeitems 放宽显示限制。
  - 如果读取了文件，请使用 state 中提供的路径，避免硬编码其它路径。
  - 确保代码可独立运行，不依赖交互输入。
- 当你需要生成图表、绘图或任何视觉化结果时，你必须严格遵循以下规则：
  - 禁止直接显示：绝对禁止调用 plt.show() 或任何其他试图打开图形界面的函数。你的运行环境是无界面的服务器。
  - 保存为文件：你必须将图表保存为 PNG 格式的图片文件。文件名必须保证全局唯一性。
  - 保存位置：图表文件必须保存到项目根目录下的 data/plots 目录中。你可以通过环境变量 PROJECT_ROOT 获取项目根目录路径。
  - 中文字体：使用中文时，必须设置微软雅黑字体：`plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']`，`plt.rcParams['axes.unicode_minus'] = False`
  - 打印访问路径：文件保存成功后，你必须立即关闭图表 (plt.close()) 以释放内存，然后以 PLOT_PATH::./data/plots/你的唯一文件名.png 的精确格式，打印出该图片的路径。"""

    # 追加更严格的分析准则，避免对年份/时间/编号做不必要的统计
    # system_prompt += (
    #     "\n分析准则（务必遵守）：\n"
    #     "1) 先用 df.head(2)、df.columns、df.dtypes 检查列名与类型，再决定分析方案。\n"
    #     "2) 默认不对‘年份/时间/编号类’字段做均值/标准差统计。以下模式视为时间/编号：列名含 year/date/time/日期/时间/年；或纯整数且取值范围像年份（1800-2100）；或列名含 id/code/编号。\n"
    #     "   - 对这类列，如需汇总仅给出唯一值个数、最小/最大值或时间范围；除非用户明确要求，否则不要把它们并入整体 describe 结果。\n"
    #     "3) 仅对与‘面积/数量/金额/比率/变化’等度量相关的数值列做统计；必要时将可解析文本列转为数值（pd.to_numeric(errors='coerce')）。\n"
    #     "4) 猜列名前先打印候选列并说明选择依据，再进行计算。\n"
    #     "5) 输出围绕洞见（趋势、异常、对比）；表格过长时先展示示例并在总结中归纳结论。\n"
    # )
    
    # 添加系统消息（使用正确的消息类型）
    messages.insert(0, SystemMessage(content=system_prompt))
    
    # 调用LLM获取回应
    response = llm.invoke(messages)
    response_content = response.content
    logger.info(f"LLM响应原文: {response_content[:500]}")
    
    # 直接解析大模型返回的JSON格式内容
    try:
        response_data = json.loads(response_content)
        thought = response_data.get("thought", "")
        action_obj = response_data.get("action", {})
        action = action_obj.get("name", "")
        action_input = action_obj.get("input")

        # 兼容旧逻辑，判断是否为代码执行或最终答案
        normalized_action = (action or "").lower()
        if not normalized_action and isinstance(action_input, dict):
            if "code" in action_input:
                normalized_action = "execute_code"
            elif "answer" in action_input:
                normalized_action = "final_answer"
        is_final_answer = normalized_action == "final_answer"

        # 状态记录
        current_step = state.get("current_step", 0) + 1
        step_record = {
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "observation": ""
        }

        intermediate_steps = state.get("intermediate_steps", [])
        intermediate_steps.append(step_record)
        state["current_step"] = current_step
        state["intermediate_steps"] = intermediate_steps
        state["action"] = action
        state["action_input"] = action_input
        state["thought"] = thought

        # 终止判断
        if is_final_answer:
            state["is_done"] = True
            if isinstance(action_input, str):
                answer_text = action_input
            elif isinstance(action_input, dict):
                answer_text = action_input.get("answer", "")
            else:
                answer_text = ""

            if answer_text:
                ai_message = AIMessage(content=answer_text)
                messages = list(state["messages"])
                messages.append(ai_message)
                state["messages"] = messages
                state["final_answer"] = answer_text
        elif not action:
            if isinstance(action_input, str):
                answer_text = action_input
            elif isinstance(action_input, dict):
                answer_text = action_input.get("answer", "")
            else:
                answer_text = ""

            if answer_text:
                ai_message = AIMessage(content=answer_text)
                messages = list(state["messages"])
                messages.append(ai_message)
                state["messages"] = messages
                state["final_answer"] = answer_text

    except Exception as e:
        logger.error(f"解析大模型JSON回复失败: {e}，原始内容: {response_content[:100]}...")
        state["error"] = f"解析大模型JSON回复失败: {e}"
        ai_message = AIMessage(content="AI回复格式解析失败，请检查大模型输出。")
        messages = list(state.get("messages", []))
        messages.append(ai_message)
        state["messages"] = messages

    return state

# 定义节点函数
def agent_node(state: AgentState) -> AgentState:
    """代理节点，分析用户指令并决定下一步操作"""
    messages = state["messages"]
    file_path = state.get("file_path")
    
    # 构建提示
    prompt = "你是一个数据分析助手。请分析用户的指令，并决定是否需要生成代码。"
    
    if file_path:
        prompt += f"\n用户上传了文件: {os.path.basename(file_path)}"
    
    # 添加提示到消息历史
    all_messages = messages + [HumanMessage(content=prompt)]
    
    # 调用LLM
    response = llm.invoke(all_messages)
    
    # 更新状态
    return {
        **state,
        "messages": messages + [response]
    }

# 安全的代码执行沙箱
def safe_code_executor(code: str, _locals: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """安全执行代码并返回结果和新变量"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    logger.info(f"创建临时目录: {temp_dir}")
    
    # 确保项目根目录下的data/plots目录存在
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    plots_dir = os.path.join(project_root, "data", "plots")
    os.makedirs(plots_dir, exist_ok=True)
    logger.info(f"确保项目plots目录存在: {plots_dir}")
    
    try:
        # 存储执行前的变量键
        original_keys = set(_locals.keys())
        
        # 如果有上传的文件，复制到临时目录
        if _locals.get("file_path") and os.path.exists(_locals["file_path"]):
            file_name = os.path.basename(_locals["file_path"])
            dest_path = os.path.join(temp_dir, file_name)
            shutil.copy2(_locals["file_path"], dest_path)
            logger.info(f"复制文件 {_locals['file_path']} 到 {dest_path}")
        
        # 写入代码到临时文件
        code_file = os.path.join(temp_dir, "code_to_execute.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)
        
        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PROJECT_ROOT"] = project_root  # 添加项目根目录环境变量
        
        # 执行代码，设置超时
        try:
            process = subprocess.Popen(
                [sys.executable, code_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,  # 改为二进制模式
                cwd=temp_dir,
                env=env
            )
            
            # 设置超时时间为30秒
            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=30)
                # 使用utf-8解码
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                execution_result = stdout
                if stderr:
                    execution_result += f"\n错误输出:\n{stderr}"
                
            except subprocess.TimeoutExpired:
                process.kill()
                execution_result = "错误: 代码执行超时（30秒）"
                
        except Exception as e:
            execution_result = f"代码执行错误: {str(e)}"
    
        # 确定执行期间创建的新变量
        # 注意：这里我们无法获取子进程中创建的变量，这只是一个占位符
        # 实际使用时，可能需要通过其他方式传递变量
        new_keys = set(_locals.keys()) - original_keys
        new_vars = {key: _locals[key] for key in new_keys}
        
        return execution_result, new_vars
        
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"清理临时目录: {temp_dir}")
        except Exception as e:
            logger.error(f"清理临时目录失败: {e}")

def execute_code_node(state: AgentState) -> AgentState:
    """执行代码节点"""
    code = state.get("code_to_execute")
    if not code:
        logger.warning("没有代码可执行")
        if state.get("intermediate_steps") and len(state["intermediate_steps"]) > 0:
            state["intermediate_steps"][-1]["observation"] = "错误：没有代码可执行"
        return state

    # 使用安全沙箱执行代码
    execution_result, new_vars = safe_code_executor(state.get("code_to_execute") or code, state)
    
    # 更新状态
    state["execution_result"] = execution_result
    if state.get("intermediate_steps") and len(state["intermediate_steps"]) > 0:
        state["intermediate_steps"][-1]["observation"] = execution_result
    state["code_to_execute"] = None

    # 将新变量添加到状态中
    for key, value in new_vars.items():
        state[key] = value
    
    return state

def final_answer_node(state: AgentState) -> AgentState:
    """生成最终回答"""
    action_input = state.get("action_input")
    if isinstance(action_input, str):
        answer = action_input
    elif isinstance(action_input, dict):
        answer = action_input.get("answer", "")
    else:
        answer = ""
    
    if answer:
        # 创建AI消息
        ai_message = AIMessage(content=answer)
        messages = list(state["messages"])
        messages.append(ai_message)
        state["messages"] = messages
        # 记录最终答案，便于前端直接读取
        state["final_answer"] = answer
    else:
        # 如果没有提供answer，生成一个基于执行结果的回复
        execution_result = state.get("execution_result", "")
        if execution_result:
            ai_message = AIMessage(content=f"代码执行完成，结果如下：\n\n{execution_result}")
            messages = list(state["messages"])
            messages.append(ai_message)
            state["messages"] = messages
    
    # 标记工作流已完成
    state["is_done"] = True
    
    return state

from langchain_core.tools import tool

# 定义工具函数
def define_tools():
    """定义可用工具"""
    
    @tool
    def read_file(file_path: str) -> str:
        """读取文件内容"""
        return read_file_content(file_path)
    
    @tool
    def detect_file_type(file_path: str) -> str:
        """检测文件类型"""
        if file_path:
            extension = os.path.splitext(file_path)[1].lower()
            if extension in ['.csv', '.xlsx', '.xls']:
                return 'data'
            elif extension in ['.py']:
                return 'python'
            elif extension in ['.js', '.ts']:
                return 'javascript'
            elif extension in ['.html']:
                return 'html'
            elif extension in ['.css']:
                return 'css'
            elif extension in ['.json']:
                return 'json'
            elif extension in ['.md']:
                return 'markdown'
            elif extension in ['.txt']:
                return 'text'
        return 'unknown'
    
    @tool
    def get_file_info(state) -> str:
        """获取当前文件信息"""
        if state.get("file_path") and state.get("file_content") and state.get("file_type"):
            return f"文件路径: {state.get('file_path')}\n文件类型: {state.get('file_type')}\n文件内容: {state.get('file_content')[:500]}..."
        elif state.get("file_path"):
            return f"文件路径: {state.get('file_path')}\n但文件内容未加载"
        else:
            return "没有文件信息"
    
    return [read_file, detect_file_type, get_file_info]

# 创建CodeAct工作流
def create_codeact_workflow(llm):
    """创建CodeAct工作流"""
    # 定义工具
    tools_list = define_tools()
    
    # 创建代码执行器
    code_act = create_codeact(llm, tools_list, safe_code_executor)
    
    # 编译工作流（不使用checkpointer）
    return code_act.compile()

async def process_query_streaming(instruction: str, file_path: Optional[str] = None, history_messages: Optional[List[Dict]] = None):
    """流式处理用户查询，实时返回每一步的思考过程"""
    import asyncio
    from typing import AsyncGenerator
    
    # 初始化对话消息
    messages: List[BaseMessage] = []

    # 将历史消息添加到对话中
    if history_messages and len(history_messages) > 0:
        for msg in history_messages:
            candidate_path = msg.get("filePath")
            if (not file_path) and candidate_path:
                is_blob_url = isinstance(candidate_path, str) and candidate_path.startswith("blob:")
                is_http_url = isinstance(candidate_path, str) and (candidate_path.startswith("http://") or candidate_path.startswith("https://"))
                looks_local = isinstance(candidate_path, str) and (os.path.isabs(candidate_path) and os.path.exists(candidate_path))
                if looks_local and (not is_blob_url) and (not is_http_url):
                    file_path = candidate_path
                    logger.info(f"从历史消息回收本地文件路径: {file_path}")

            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg.get("content", "")))
            elif msg.get("role") == "system":
                messages.append(SystemMessage(content=msg.get("content", "")))

    # 将文件上下文注入为系统消息
    if file_path and os.path.exists(file_path):
        try:
            file_name = os.path.basename(file_path)
            file_type = detect_file_type(file_path)
            system_message = (
                f"你有一个文件需要处理:\n"
                f"文件名: {file_name}\n"
                f"文件类型: {file_type}\n"
                f"文件路径: {file_path}")
            messages.append(SystemMessage(content=system_message))
            logger.info(f"成功添加文件信息到系统消息: {file_path}")
        except Exception as e:
            logger.error(f"处理文件时出错: {str(e)}")

    # 添加用户消息
    messages.append(HumanMessage(content=instruction))

    # 初始化状态
    state: AgentState = {
        "messages": messages,
        "file_path": file_path,
        "file_content": None,
        "file_type": detect_file_type(file_path) if file_path and os.path.exists(file_path) else None,
        "code_to_execute": None,
        "execution_result": None,
        "intermediate_steps": [],
        "current_step": 0,
        "max_iterations": 10,
        "action": None,
        "action_input": None,
        "observation": None,
        "is_done": False,
    }

    try:
        # 迭代式 ReAct 回路，每一步都流式返回
        for iteration in range(state.get("max_iterations", 5)):
            # 发送步骤开始信号
            yield {
                "type": "step_start",
                "step": iteration + 1,
                "message": f"🤔 开始第 {iteration + 1} 步思考..."
            }

            # 1) 让 Agent 分析并给出"思考/行动/行动输入"
            state = react_agent_node(state)
            
            # 获取当前步骤信息
            current_step = state.get("intermediate_steps", [])[-1] if state.get("intermediate_steps") else {}
            thought = current_step.get("thought", "")
            action = current_step.get("action", "")
            action_input = current_step.get("action_input", {})

            # 流式返回思考过程
            if thought:
                yield {
                    "type": "thought",
                    "step": iteration + 1,
                    "content": thought
                }

            # 流式返回行动
            if action:
                yield {
                    "type": "action",
                    "step": iteration + 1,
                    "action": action,
                    "action_input": action_input
                }

            action_text = (state.get("action") or "").lower().strip()
            normalized_action = re.sub(r"[^a-z_]+", "", action_text)

            # 2) 根据行动执行
            # 检查是否已经完成（在react_agent_node中设置）
            if state.get("is_done", False):
                # 如果没有行动或者是final_answer，直接返回最终答案
                if not action_text or (normalized_action == "final_answer") or ("final_answer" in action_text):
                    # 获取最终答案
                    messages_out = state.get("messages", [])
                    ai_messages = [m for m in messages_out if isinstance(m, AIMessage)]
                    final_response = ai_messages[-1].content if ai_messages else "任务已完成"
                    
                    # 获取所有历史执行结果
                    all_execution_results = []
                    for step in state.get("intermediate_steps", []):
                        if "observation" in step and step["observation"]:
                            all_execution_results.append(step["observation"])
                    
                    # 获取最近一次的LLM思考和代码执行结果
                    last_thought = thought if thought else ""
                    
                    # 调用makeReport函数生成报告，并将其作为最终答案
                    try:
                        report_md = makeReport(last_thought, all_execution_results)
                        print(report_md) # debug
                        # 输出报告作为最终答案
                        yield {
                            "type": "final_answer",
                            "step": iteration + 1,
                            "content": report_md
                        }
                    except Exception as e:
                        logger.error(f"生成报告失败: {str(e)}")
                        # 如果报告生成失败，回退到原始的最终答案
                        yield {
                            "type": "final_answer",
                            "step": iteration + 1,
                            "content": final_response
                        }
                    break

            # 2.1) 最终回答
            if isinstance(action_input, str):
                answer_candidate = action_input.strip()
            elif isinstance(action_input, dict):
                answer_candidate = action_input.get("answer", "")
            else:
                answer_candidate = ""

            is_final_answer = (
                (normalized_action == "final_answer") or
                ("final_answer" in action_text) or
                (not action_text and answer_candidate)
            )
            if is_final_answer:
                state = final_answer_node(state)
                
                # 获取所有历史执行结果
                all_execution_results = []
                for step in state.get("intermediate_steps", []):
                    if "observation" in step and step["observation"]:
                        all_execution_results.append(step["observation"])
                
                # 获取最近一次的LLM思考和代码执行结果
                last_thought = thought if thought else ""
                
                # 调用makeReport函数生成报告，并将其作为最终答案
                try:
                    report_md = makeReport(last_thought, all_execution_results)
                    print(report_md) # debug
                    # 输出报告作为最终答案
                    yield {
                        "type": "final_answer",
                        "step": iteration + 1,
                        "content": report_md
                    }
                except Exception as e:
                    logger.error(f"生成报告失败: {str(e)}")
                    # 如果报告生成失败，回退到原始的最终答案
                    final_answer = state.get("final_answer") or ""
                    if final_answer:
                        yield {
                            "type": "final_answer",
                            "step": iteration + 1,
                            "content": final_answer
                        }
                break

            # 2.2) 只保留 execute_code 相关判断
            if ("执行代码" in action_text) or (normalized_action in ("execute_code",)) or ("execute_code" in action_text):
                # 流式显示代码执行开始
                if isinstance(action_input, str):
                    code = action_input
                elif isinstance(action_input, dict):
                    code = action_input.get("code")
                else:
                    code = None
                if code:
                    state["code_to_execute"] = code
                    print(f"----------\n{code}\n----------")
                    yield {
                        "type": "code_execution_start",
                        "step": iteration + 1,
                        "code": code
                    }
                # 执行代码
                state = execute_code_node(state)
                # 流式返回执行结果
                execution_result = state.get("execution_result") or "(无输出)"
                yield {
                    "type": "code_execution_result",
                    "step": iteration + 1,
                    "result": execution_result
                }
                # 更新观察结果
                if state.get("intermediate_steps") and len(state["intermediate_steps"]) > 0:
                    state["intermediate_steps"][-1]["observation"] = execution_result
                # 流式返回观察
                yield {
                    "type": "observation",
                    "step": iteration + 1,
                    "content": execution_result
                }
                # 将执行结果反馈为"观察"，继续下一轮对话
                state_messages = list(state["messages"])
                state_messages.append(HumanMessage(content=f"观察:\n{execution_result}\n\n请根据观察更新你的计划或给出最终答案。"))
                state["messages"] = state_messages
                continue

            # 其他动作，直接继续下一轮
            continue

        # 如果没有最终答案，生成一个总结
        if not state.get("final_answer"):
            messages_out: List[BaseMessage] = state.get("messages", [])
            ai_messages = [m for m in messages_out if isinstance(m, AIMessage)]
            response_text = ai_messages[-1].content if ai_messages else f"收到指令：'{instruction}'。"
            
            if state.get("execution_result"):
                if not response_text.endswith("\n"):
                    response_text += "\n\n"
                response_text += f"代码执行结果：\n\n{state.get('execution_result')}"

            yield {
                "type": "final_response",
                "content": response_text,
                "intermediate_steps": state.get("intermediate_steps", []),
                "execution_result": state.get("execution_result"),
                "file_path": state.get("file_path")
            }

    except Exception as e:
        logger.error(f"流式处理查询失败: {e}")
        yield {
            "type": "error",
            "message": f"处理失败: {str(e)}"
        }

def makeReport(last_thought, all_execution_results):
    """
    生成任务执行报告，包含思考过程和执行结果
    
    Args:
        last_thought (str): 最后一次LLM的思考内容
        all_execution_results (list): 所有历史步骤的执行结果列表
        
    Returns:
        str: Markdown格式的报告内容
    """
    # 提示词模板
    prompt_template = """
    你是一个数据分析助手，请根据以下信息生成一份Markdown格式的报告：
    历史分析过程如下
    {thought}
    历史代码执行结果如下
    {results}
    请生成一份结构清晰的Markdown报告，必要时附带上图片
    注意，你只需要以Markdown格式的文本返回报告,不需要任何语法的包裹。
    """
    
    try:
        # 第一次尝试：使用所有执行结果
        all_results_text = "\n\n".join([f"步骤 {i+1}:\n```\n{result}\n```" for i, result in enumerate(all_execution_results) if result])
        prompt = prompt_template.format(thought=last_thought, results=all_results_text)
        
        # 调用AI生成报告
        return llm.invoke(prompt).content
    except Exception as e:
        logger.warning(f"使用全部执行结果生成报告失败: {str(e)}，尝试使用后半部分结果")
        
        try:
            # 第二次尝试：使用后半部分执行结果
            half_index = len(all_execution_results) // 2
            half_results = all_execution_results[half_index:]
            half_results_text = "\n\n".join([f"步骤 {i+half_index+1}:\n```\n{result}\n```" for i, result in enumerate(half_results) if result])
            prompt = prompt_template.format(thought=last_thought, results=half_results_text)
            
            # 调用AI生成报告
            return llm.invoke(prompt).content
        except Exception as e:
            logger.warning(f"使用后半部分执行结果生成报告失败: {str(e)}，尝试仅使用最后一次执行结果")
            
            try:
                # 第三次尝试：仅使用最后一次执行结果
                if all_execution_results and len(all_execution_results) > 0:
                    last_result = all_execution_results[-1]
                    last_result_text = f"最终结果:\n```\n{last_result}\n```"
                    prompt = prompt_template.format(thought=last_thought, results=last_result_text)
                    
                    # 调用AI生成报告
                    return llm.invoke(prompt).content
                else:
                    # 没有执行结果
                    prompt = prompt_template.format(thought=last_thought, results="没有执行结果。")
                    return llm.invoke(prompt).content
            except Exception as e:
                logger.error(f"生成报告最终失败: {str(e)}")
                return f"# 报告生成失败\n\n生成报告时发生错误: {str(e)}"

# def process_query(instruction: str, file_path: Optional[str] = None, history_messages: Optional[List[Dict]] = None) -> Dict:
#     """处理用户查询：理解需求→生成/执行代码→基于结果回答（ReAct 回路）"""
#     # 初始化对话消息
#     messages: List[BaseMessage] = []

#     # 将历史消息添加到对话中
#     if history_messages and len(history_messages) > 0:
#         # 将历史消息转换为LangChain消息格式
#         for msg in history_messages:
#             # 回收文件路径：优先使用助手消息返回的真实本地路径
#             candidate_path = msg.get("filePath")
#             if (not file_path) and candidate_path:
#                 # 过滤掉浏览器的 blob: URL 或非本地绝对路径，避免错误路径污染
#                 is_blob_url = isinstance(candidate_path, str) and candidate_path.startswith("blob:")
#                 is_http_url = isinstance(candidate_path, str) and (candidate_path.startswith("http://") or candidate_path.startswith("https://"))
#                 looks_local = isinstance(candidate_path, str) and (os.path.isabs(candidate_path) and os.path.exists(candidate_path))
#                 if looks_local and (not is_blob_url) and (not is_http_url):
#                     file_path = candidate_path
#                     logger.info(f"从历史消息回收本地文件路径: {file_path}")
#                 else:
#                     # 忽略非本地/无效路径
#                     pass

#             if msg.get("role") == "user":
#                 messages.append(HumanMessage(content=msg.get("content", "")))
#             elif msg.get("role") == "assistant":
#                 messages.append(AIMessage(content=msg.get("content", "")))
#             elif msg.get("role") == "system":
#                 messages.append(SystemMessage(content=msg.get("content", "")))

#     # 将文件上下文注入为系统消息，便于模型感知
#     file_content: Optional[str] = None
#     file_type: Optional[str] = None
#     if file_path and os.path.exists(file_path):
#         try:
#             file_name = os.path.basename(file_path)
#             file_type = detect_file_type(file_path)
#             # 不直接注入二进制内容，改为提供路径与类型
#             system_message = (
#                 f"你有一个文件需要处理:\n"
#                 f"文件名: {file_name}\n"
#                 f"文件类型: {file_type}\n"
#                 f"文件路径: {file_path}")
#             messages.append(SystemMessage(content=system_message))
#             logger.info(f"成功添加文件信息到系统消息: {file_path}")
#         except Exception as e:
#             logger.error(f"处理文件时出错: {str(e)}")

#     # 添加用户消息
#     messages.append(HumanMessage(content=instruction))

#     # 初始化状态
#     state: AgentState = {
#         "messages": messages,
#         "file_path": file_path,
#         "file_content": None,
#         "file_type": detect_file_type(file_path) if file_path and os.path.exists(file_path) else None,
#         "code_to_execute": None,
#         "execution_result": None,
#         "intermediate_steps": [],
#         "current_step": 0,
#         "max_iterations": 10,
#         "action": None,
#         "action_input": None,
#         "observation": None,
#         "is_done": False,
#     }

#     try:
#         # 迭代式 ReAct 回路
#         for _ in range(state.get("max_iterations", 5)):
#             # 1) 让 Agent 分析并给出"思考/行动/行动输入"
#             state = react_agent_node(state)

#             action_text = (state.get("action") or "").lower().strip()
#             # 规范化行动标记，去掉括号/空格等，如 "[final_answer]" → "final_answer"
#             normalized_action = re.sub(r"[^a-z_]+", "", action_text)

#             # 2) 根据行动执行
#             if not action_text:
#                 # 无行动，继续下一轮，直到达到上限
#                 continue

#             # 2.1) 最终回答
#             if (normalized_action == "final_answer") or ("final_answer" in action_text):
#                 state = final_answer_node(state)
#                 break

#             # 2.2) 生成并/或执行代码（中文"执行代码"或英文 execute_code）
#             if ("执行代码" in action_text) or (normalized_action in ("execute_code", "generate_code")) or ("execute_code" in action_text) or ("generate_code" in action_text):
#                 # 如果上一步从 LLM 提取到了代码，放入待执行
#                 action_input = state.get("action_input") or {}
#                 code = action_input.get("code") if isinstance(action_input, dict) else None
#                 if code:
#                     state["code_to_execute"] = code
#                 # 执行代码
#                 state = execute_code_node(state)

#                 # 将执行结果反馈为"观察"，继续下一轮对话
#                 observation_text = state.get("execution_result") or "(无输出)"
#                 state_messages = list(state["messages"])  # type: ignore
#                 state_messages.append(HumanMessage(content=f"观察:\n{observation_text}\n\n请根据观察更新你的计划或给出最终答案。"))
#                 state["messages"] = state_messages
#                 continue

#             # 其他动作，直接继续下一轮
#             continue

#         # 组织返回
#         messages_out: List[BaseMessage] = state.get("messages", [])  # type: ignore
#         intermediate_steps = state.get("intermediate_steps", [])

#         # 取最后一个 AI 回复作为总体回复
#         ai_messages = [m for m in messages_out if isinstance(m, AIMessage)]
#         response_text = ai_messages[-1].content if ai_messages else f"收到指令：'{instruction}'。"

#         # 如有执行结果，附加到响应（即使未显式触发 final_answer 也展示）
#         if state.get("execution_result"):
#             if not response_text.endswith("\n"):
#                 response_text += "\n\n"
#             response_text += f"代码执行结果：\n\n{state.get('execution_result')}"

#         # 如果仍然没有可读信息，回退展示最后一步思考/行动/观察摘要
#         if (not ai_messages) and (not state.get("execution_result")):
#             last_step = intermediate_steps[-1] if intermediate_steps else None
#             if last_step:
#                 summary = (
#                     f"思考: {last_step.get('thought', '')}\n"
#                     f"行动: {last_step.get('action', '')}\n"
#                     f"观察: {str(last_step.get('observation', ''))[:800]}"
#                 )
#                 if not response_text.endswith("\n"):
#                     response_text += "\n\n"
#                 response_text += summary

#         final_answer_val = state.get("final_answer")
#         return {
#             "response": final_answer_val or response_text,
#             "final_answer": final_answer_val,
#             "intermediate_steps": intermediate_steps,
#             "execution_result": state.get("execution_result"),
#             "file_path": state.get("file_path"),
#         }
#     except Exception as e:
#         logger.error(f"处理查询失败: {e}")
#         return {
#             "response": f"处理失败: {str(e)}",
#             "intermediate_steps": [],
#             "execution_result": None,
#         }
