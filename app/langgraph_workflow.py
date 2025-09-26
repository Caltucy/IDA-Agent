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
    action_input: Optional[Dict[str, Any]]
    observation: Optional[str]
    is_done: bool

# 初始化LLM
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"), temperature=0)

# 定义工具函数
def read_file_content(file_path):
    """读取文件内容：二进制类型直接按二进制返回长度，其它尝试多种编码"""
    binary_exts = {'.xlsx', '.xls', '.xlsb', '.xlsm', '.parquet', '.feather'}
    try:
        ext = os.path.splitext(file_path)[1].lower()
    except Exception:
        ext = ''

    if ext in binary_exts:
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            logger.info(f"以二进制方式读取文件: {file_path}")
            return f"[二进制文件，长度: {len(data)} 字节]"
        except Exception as e:
            logger.error(f"读取二进制文件失败: {e}")
            return f"读取文件失败: {e}"

    encodings = ['utf-8', 'gbk', 'cp936', 'gb18030', 'latin1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            logger.info(f"成功使用 {encoding} 编码读取文件: {file_path}")
            return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return f"读取文件失败: {e}"
    
    # 如果所有编码都失败，尝试以二进制方式读取
    try:
        with open(file_path, 'rb') as file:
            binary_content = file.read()
        logger.warning(f"以二进制方式读取文件: {file_path}")
        return f"[二进制文件，长度: {len(binary_content)} 字节]"
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return f"读取文件失败: {e}"

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
            action_input = step.get("action_input", {})
            observation = step.get("observation", "")
            
            steps_history += f"步骤 {i+1}:\n思考: {thought}\n行动: {action}\n行动输入: {json.dumps(action_input, ensure_ascii=False)}\n观察: {observation}\n\n"
    
    # 构建系统提示
    system_prompt = f"""你是一个数据分析助手，使用ReAct（思考-行动）方法解决问题。
你可以使用以下工具:
1. generate_code: 生成Python代码来分析或处理数据
2. execute_code: 执行生成的代码并获取结果
3. final_answer: 提供最终答案，结束对话

{file_info if file_info else ""}

{steps_history if steps_history else ""}

按照以下格式回应:
思考: 分析问题并思考解决方案
行动: [工具名称]
行动输入: {{
  "code": "要执行的Python代码" // 如果使用generate_code或execute_code
  "answer": "最终答案" // 如果使用final_answer
}}

当你有足够信息回答用户问题时，使用final_answer工具。
\n代码生成要求:\n- 使用 pandas/numpy 等库处理数据时，务必使用 print 打印关键结果。\n- 打印表格/序列前，设置完整显示选项: \n  pandas: display.max_rows=None, display.max_columns=None, display.max_colwidth=None, display.width=None。\n- DataFrame/Series 请优先使用 to_string() 打印完整内容。\n- numpy 如需打印数组，可设置 threshold/edgeitems 放宽显示限制。\n- 如果读取了文件，请使用 state 中提供的路径，避免硬编码其它路径。\n- 确保代码可独立运行，不依赖交互输入。\n"""

    # 追加更严格的分析准则，避免对年份/时间/编号做不必要的统计
    system_prompt += (
        "\n分析准则（务必遵守）：\n"
        "1) 先用 df.head(2)、df.columns、df.dtypes 检查列名与类型，再决定分析方案。\n"
        "2) 默认不对‘年份/时间/编号类’字段做均值/标准差统计。以下模式视为时间/编号：列名含 year/date/time/日期/时间/年；或纯整数且取值范围像年份（1800-2100）；或列名含 id/code/编号。\n"
        "   - 对这类列，如需汇总仅给出唯一值个数、最小/最大值或时间范围；除非用户明确要求，否则不要把它们并入整体 describe 结果。\n"
        "3) 仅对与‘面积/数量/金额/比率/变化’等度量相关的数值列做统计；必要时将可解析文本列转为数值（pd.to_numeric(errors='coerce')）。\n"
        "4) 猜列名前先打印候选列并说明选择依据，再进行计算。\n"
        "5) 输出围绕洞见（趋势、异常、对比）；表格过长时先展示示例并在总结中归纳结论。\n"
    )
    
    # 添加系统消息（使用正确的消息类型）
    messages.insert(0, SystemMessage(content=system_prompt))
    
    # 调用LLM获取回应
    response = llm.invoke(messages)
    response_content = response.content
    logger.info(f"LLM响应原文: {response_content[:500]}")
    
    # 解析回应
    thought = ""
    action = ""
    action_input = {}
    
    # 提取思考部分
    thought_match = response_content.split("思考:", 1)
    if len(thought_match) > 1:
        thought_text = thought_match[1].split("行动:", 1)[0].strip()
        thought = thought_text
    
    # 提取行动部分
    action_match = response_content.split("行动:", 1)
    if len(action_match) > 1:
        action_text = action_match[1].split("行动输入:", 1)[0].strip()
        action = action_text
    
    # 提取行动输入
    action_input_match = response_content.split("行动输入:", 1)
    if len(action_input_match) > 1:
        action_input_text = action_input_match[1].strip()
        
        # 规范化行动标记，支持 [generate_code]/[execute_code]/[final_answer]
        normalized_action = re.sub(r"[^a-z_]+", "", (action or "").lower())

        # 是否为代码型行动
        is_code_action = (
            ("执行代码" in (action or "")) or
            (normalized_action in ("generate_code", "execute_code")) or
            ("generate_code" in (action or "")) or
            ("execute_code" in (action or ""))
        )

        if is_code_action:
            # 优先处理 ```python 代码块
            code_start = action_input_text.find("```python")
            if code_start >= 0:
                code_start += 9
                code_end = action_input_text.find("```", code_start)
                if code_end > code_start:
                    code = action_input_text[code_start:code_end].strip()
                    action_input = {"code": code}
                else:
                    action_input = {"code": action_input_text.strip()}
            else:
                # 尝试从 "code": "..." 结构中用正则宽松提取，支持换行
                try:
                    m = re.search(r'"code"\s*:\s*"([\s\S]*?)"\s*\}?\s*$', action_input_text)
                    if m:
                        raw = m.group(1)
                        # 处理常见转义
                        raw = raw.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r').replace('\\"', '"')
                        action_input = {"code": raw}
                    else:
                        # 退路：直接使用全文
                        action_input = {"code": action_input_text.strip()}
                except Exception:
                    action_input = {"code": action_input_text.strip()}
        else:
            # 非代码执行操作，尝试解析JSON（宽松清理控制符）
            try:
                json_start = action_input_text.find("{")
                json_end = action_input_text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = action_input_text[json_start:json_end]
                    json_str = ''.join(ch for ch in json_str if ord(ch) >= 32 or ch in '\n\r\t')
                    action_input = json.loads(json_str)
            except Exception as e:
                logger.error(f"解析行动输入失败: {e}，原始输入: {action_input_text[:100]}...")
                action_input = {"error": "解析失败", "raw_text": action_input_text}
    
    # 更新状态
    current_step = state.get("current_step", 0) + 1
    
    # 记录这一步
    step_record = {
        "thought": thought,
        "action": action,
        "action_input": action_input,
        "observation": ""  # 将在后续步骤中填充
    }
    
    intermediate_steps = state.get("intermediate_steps", [])
    intermediate_steps.append(step_record)
    
    # 更新状态
    state["current_step"] = current_step
    state["intermediate_steps"] = intermediate_steps
    state["action"] = action
    state["action_input"] = action_input
    state["thought"] = thought
    try:
        code_preview = (action_input.get("code", "") if isinstance(action_input, dict) else "")
        logger.info(f"解析行动: action='{action}', 代码长度={len(code_preview)}")
    except Exception:
        pass
    
    # 检查是否完成或者没有行动（直接回复）
    if (action and action.strip().lower() == "final_answer") or not action:
        state["is_done"] = True
        
        # 如果是final_answer且有answer字段，使用answer作为回复
        if action and action.strip().lower() == "final_answer" and "answer" in action_input:
            ai_message = AIMessage(content=action_input["answer"])
            messages = list(state["messages"])
            messages.append(ai_message)
            state["messages"] = messages
        # 如果没有行动，直接使用LLM的回复作为最终回复
        elif not action:
            ai_message = AIMessage(content=response_content)
            messages = list(state["messages"])
            messages.append(ai_message)
            state["messages"] = messages
    
    return state
# 已在文件顶部初始化过 llm，这里移除重复定义

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

def should_generate_code(state: AgentState) -> str:
    """决定是否需要生成代码"""
    last_message = state["messages"][-1]
    content = last_message.content.lower()
    
    # 简单的判断逻辑，实际应用中可能需要更复杂的分析
    if "生成代码" in content or "写代码" in content or "代码示例" in content:
        return "generateCode"
    else:
        return "reply"

def generate_code_node(state: AgentState) -> AgentState:
    """生成代码节点"""
    action_input = state.get("action_input", {})
    code = action_input.get("code", "")
    
    if code:
        state["code_to_execute"] = code
        
        # 记录观察结果
        if state.get("intermediate_steps") and len(state["intermediate_steps"]) > 0:
            state["intermediate_steps"][-1]["observation"] = "代码已生成，准备执行"
    else:
        # 如果没有提供代码，记录错误
        if state.get("intermediate_steps") and len(state["intermediate_steps"]) > 0:
            state["intermediate_steps"][-1]["observation"] = "错误：未提供代码"
    
    return state

# 安全的代码执行沙箱
def safe_code_executor(code: str, _locals: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """安全执行代码并返回结果和新变量"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    logger.info(f"创建临时目录: {temp_dir}")
    
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
    
    # 如果代码未显式打印结果，尝试为常见结果变量补充打印
    try:
        code_str = str(code)
        needs_print = ("print(" not in code_str)
        if needs_print:
            candidate_vars = ["summary", "result", "results", "output"]
            chosen = None
            for var in candidate_vars:
                # 粗略判断变量是否在代码中被赋值或使用
                if re.search(rf"\b{var}\b", code_str):
                    chosen = var
                    break
            if chosen:
                code_str += f"\nprint({chosen})\n"
            else:
                code_str += "\nprint(\"代码已执行，无输出（未检测到可打印变量）\")\n"
            state["code_to_execute"] = code_str
    except Exception as _e:
        # 不中断执行，按原代码继续
        pass

    # 使用安全沙箱执行代码
    execution_result, new_vars = safe_code_executor(state.get("code_to_execute") or code, state)
    
    # 更新状态
    state["execution_result"] = execution_result
    if state.get("intermediate_steps") and len(state["intermediate_steps"]) > 0:
        state["intermediate_steps"][-1]["observation"] = execution_result
    
    # 将新变量添加到状态中
    for key, value in new_vars.items():
        state[key] = value
    
    return state

def final_answer_node(state: AgentState) -> AgentState:
    """生成最终回答"""
    action_input = state.get("action_input", {})
    answer = action_input.get("answer", "")
    
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
                    
                    yield {
                        "type": "final_answer",
                        "step": iteration + 1,
                        "content": final_response
                    }
                    break

            # 2.1) 最终回答
            if (normalized_action == "final_answer") or ("final_answer" in action_text):
                state = final_answer_node(state)
                
                # 流式返回最终答案
                final_answer = state.get("final_answer") or ""
                if final_answer:
                    yield {
                        "type": "final_answer",
                        "step": iteration + 1,
                        "content": final_answer
                    }
                break

            # 2.2) 生成并/或执行代码
            if ("执行代码" in action_text) or (normalized_action in ("execute_code", "generate_code")) or ("execute_code" in action_text) or ("generate_code" in action_text):
                # 流式显示代码执行开始
                code = action_input.get("code") if isinstance(action_input, dict) else None
                if code:
                    state["code_to_execute"] = code
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

def process_query(instruction: str, file_path: Optional[str] = None, history_messages: Optional[List[Dict]] = None) -> Dict:
    """处理用户查询：理解需求→生成/执行代码→基于结果回答（ReAct 回路）"""
    # 初始化对话消息
    messages: List[BaseMessage] = []

    # 将历史消息添加到对话中
    if history_messages and len(history_messages) > 0:
        # 将历史消息转换为LangChain消息格式
        for msg in history_messages:
            # 回收文件路径：优先使用助手消息返回的真实本地路径
            candidate_path = msg.get("filePath")
            if (not file_path) and candidate_path:
                # 过滤掉浏览器的 blob: URL 或非本地绝对路径，避免错误路径污染
                is_blob_url = isinstance(candidate_path, str) and candidate_path.startswith("blob:")
                is_http_url = isinstance(candidate_path, str) and (candidate_path.startswith("http://") or candidate_path.startswith("https://"))
                looks_local = isinstance(candidate_path, str) and (os.path.isabs(candidate_path) and os.path.exists(candidate_path))
                if looks_local and (not is_blob_url) and (not is_http_url):
                    file_path = candidate_path
                    logger.info(f"从历史消息回收本地文件路径: {file_path}")
                else:
                    # 忽略非本地/无效路径
                    pass

            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg.get("content", "")))
            elif msg.get("role") == "system":
                messages.append(SystemMessage(content=msg.get("content", "")))

    # 将文件上下文注入为系统消息，便于模型感知
    file_content: Optional[str] = None
    file_type: Optional[str] = None
    if file_path and os.path.exists(file_path):
        try:
            file_name = os.path.basename(file_path)
            file_type = detect_file_type(file_path)
            # 不直接注入二进制内容，改为提供路径与类型
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
        # 迭代式 ReAct 回路
        for _ in range(state.get("max_iterations", 5)):
            # 1) 让 Agent 分析并给出"思考/行动/行动输入"
            state = react_agent_node(state)

            action_text = (state.get("action") or "").lower().strip()
            # 规范化行动标记，去掉括号/空格等，如 "[final_answer]" → "final_answer"
            normalized_action = re.sub(r"[^a-z_]+", "", action_text)

            # 2) 根据行动执行
            if not action_text:
                # 无行动，继续下一轮，直到达到上限
                continue

            # 2.1) 最终回答
            if (normalized_action == "final_answer") or ("final_answer" in action_text):
                state = final_answer_node(state)
                break

            # 2.2) 生成并/或执行代码（中文"执行代码"或英文 execute_code）
            if ("执行代码" in action_text) or (normalized_action in ("execute_code", "generate_code")) or ("execute_code" in action_text) or ("generate_code" in action_text):
                # 如果上一步从 LLM 提取到了代码，放入待执行
                action_input = state.get("action_input") or {}
                code = action_input.get("code") if isinstance(action_input, dict) else None
                if code:
                    state["code_to_execute"] = code
                # 执行代码
                state = execute_code_node(state)

                # 将执行结果反馈为"观察"，继续下一轮对话
                observation_text = state.get("execution_result") or "(无输出)"
                state_messages = list(state["messages"])  # type: ignore
                state_messages.append(HumanMessage(content=f"观察:\n{observation_text}\n\n请根据观察更新你的计划或给出最终答案。"))
                state["messages"] = state_messages
                continue

            # 其他动作，直接继续下一轮
            continue

        # 组织返回
        messages_out: List[BaseMessage] = state.get("messages", [])  # type: ignore
        intermediate_steps = state.get("intermediate_steps", [])

        # 取最后一个 AI 回复作为总体回复
        ai_messages = [m for m in messages_out if isinstance(m, AIMessage)]
        response_text = ai_messages[-1].content if ai_messages else f"收到指令：'{instruction}'。"

        # 如有执行结果，附加到响应（即使未显式触发 final_answer 也展示）
        if state.get("execution_result"):
            if not response_text.endswith("\n"):
                response_text += "\n\n"
            response_text += f"代码执行结果：\n\n{state.get('execution_result')}"

        # 如果仍然没有可读信息，回退展示最后一步思考/行动/观察摘要
        if (not ai_messages) and (not state.get("execution_result")):
            last_step = intermediate_steps[-1] if intermediate_steps else None
            if last_step:
                summary = (
                    f"思考: {last_step.get('thought', '')}\n"
                    f"行动: {last_step.get('action', '')}\n"
                    f"观察: {str(last_step.get('observation', ''))[:800]}"
                )
                if not response_text.endswith("\n"):
                    response_text += "\n\n"
                response_text += summary

        final_answer_val = state.get("final_answer")
        return {
            "response": final_answer_val or response_text,
            "final_answer": final_answer_val,
            "intermediate_steps": intermediate_steps,
            "execution_result": state.get("execution_result"),
            "file_path": state.get("file_path"),
        }
    except Exception as e:
        logger.error(f"处理查询失败: {e}")
        return {
            "response": f"处理失败: {str(e)}",
            "intermediate_steps": [],
            "execution_result": None,
        }