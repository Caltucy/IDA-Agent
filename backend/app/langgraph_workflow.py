from typing import Dict, TypedDict, Annotated, Sequence, List, Optional, Literal, Union, Any
import os, sys, json, logging, tempfile, shutil, subprocess, time, re, ast, contextlib, io, builtins
from langgraph.prebuilt import ToolNode
try:
    from langgraph_codeact import create_codeact  # 可选依赖
except Exception:
    def create_codeact(llm, tools_list, safe_executor):
        raise ImportError("缺少可选依赖 'langgraph_codeact'。相关高级功能未启用，但不影响基础 API 运行。")
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
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置一个支持中文的字体，'SimHei'是黑体
plt.rcParams['axes.unicode_minus'] = False 
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

# 初始化LLM - 优化网络连接
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"), 
    temperature=0,
    max_retries=3,  # 增加重试次数
    request_timeout=60,  # 增加请求超时时间
    max_tokens=4000  # 限制响应长度，减少网络传输
)

# 缓存机制，避免重复处理
_file_cache = {}
_query_cache = {}

def clear_cache():
    """清理缓存，避免内存泄漏"""
    global _file_cache, _query_cache
    _file_cache.clear()
    _query_cache.clear()
    logger.info("缓存已清理")

def check_network_connection():
    """检查网络连接状态"""
    try:
        import requests
        response = requests.get("https://api.ganjiuwanshi.com/v1", timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"网络连接检查失败: {e}")
        return False

# 定义工具函数
def read_file_content(file_path, max_size_mb=10, preview_lines=100):
    """优化文件读取：大文件只读取预览，避免重复读取"""
    # 检查缓存
    if file_path in _file_cache:
        logger.info(f"从缓存读取文件: {file_path}")
        return _file_cache[file_path]
    
    binary_exts = {'.xlsx', '.xls', '.xlsb', '.xlsm', '.parquet', '.feather'}
    try:
        ext = os.path.splitext(file_path)[1].lower()
    except Exception:
        ext = ''

    # 检查文件大小
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    
    if ext in binary_exts:
        if file_size_mb > max_size_mb:
            logger.info(f"大文件 {file_path} ({file_size_mb:.1f}MB)，仅返回文件信息")
            result = f"[Excel/二进制文件，大小: {file_size_mb:.1f}MB，路径: {file_path}]"
        else:
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                logger.info(f"以二进制方式读取文件: {file_path}")
                result = f"[二进制文件，长度: {len(data)} 字节]"
            except Exception as e:
                logger.error(f"读取二进制文件失败: {e}")
                result = f"读取文件失败: {e}"
    else:
        # 文本文件处理
        if file_size_mb > max_size_mb:
            logger.info(f"大文本文件 {file_path} ({file_size_mb:.1f}MB)，只读取前{preview_lines}行")
            result = _read_large_text_file(file_path, preview_lines)
        else:
            result = _read_small_text_file(file_path)
    
    # 缓存结果
    _file_cache[file_path] = result
    return result

def _read_large_text_file(file_path, preview_lines):
    """读取大文本文件的前几行"""
    encodings = ['utf-8', 'gbk', 'cp936', 'gb18030', 'latin1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                lines = []
                for i, line in enumerate(file):
                    if i >= preview_lines:
                        break
                    lines.append(line.rstrip('\n\r'))
                content = '\n'.join(lines)
                logger.info(f"成功使用 {encoding} 编码读取大文件前{preview_lines}行: {file_path}")
                return f"[文件预览，前{preview_lines}行]\n{content}\n\n[文件较大，完整内容请通过代码读取]"
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"读取大文件失败: {e}")
            return f"读取文件失败: {e}"
    
    return f"[大文件，无法读取内容，路径: {file_path}]"

def _read_small_text_file(file_path):
    """读取小文本文件"""
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
    
    # 添加文件信息（如果有）- 优化：避免重复读取
    file_info = ""
    if state.get("file_path"):
        file_path = state["file_path"]
        file_type = state.get("file_type") or detect_file_type(file_path)
        file_content = state.get("file_content")
        
        # 只在第一次或文件内容为空时才读取
        if not file_content and os.path.exists(file_path):
            file_content = read_file_content(file_path)
            state["file_content"] = file_content
            state["file_type"] = file_type
        
        if file_content:
            # 对于大文件，只显示基本信息，避免在提示中重复大内容
            if len(file_content) > 2000:
                file_info = f"文件路径: {file_path}\n文件类型: {file_type}\n文件大小: {len(file_content)} 字符\n[文件内容已加载，可通过代码访问]\n"
            else:
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
    
    # 构建系统提示 - 优化版本，减少冗余信息
    system_prompt = f"""你是一个数据分析助手，使用ReAct（思考-行动）方法解决问题。

可用工具:
1. execute_code: 执行Python代码分析数据
2. final_answer: 提供最终答案

{file_info if file_info else ""}

{steps_history if steps_history else ""}

格式:
思考: 分析问题
行动: execute_code 或 final_answer
行动输入: {{"code": "Python代码"}} 或 {{"answer": "答案"}}

代码要求:
- 使用print()输出关键结果
- 设置pandas显示选项: pd.set_option('display.max_rows', None)
- 文件路径已提供为file_path变量
- 确保代码可独立运行

优先直接生成可执行的完整代码，避免多次迭代。"""

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
    
    # 调用LLM获取回应 - 添加重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = llm.invoke(messages)
            response_content = response.content
            logger.info(f"LLM响应成功 (尝试 {attempt + 1}): {response_content[:500]}")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 递增等待时间
                logger.warning(f"LLM调用失败 (尝试 {attempt + 1}/{max_retries}): {e}，{wait_time}秒后重试")
                time.sleep(wait_time)
            else:
                logger.error(f"LLM调用最终失败: {e}")
                # 返回错误响应
                error_message = f"网络连接失败，请检查网络设置或稍后重试。错误详情: {str(e)}"
                ai_message = AIMessage(content=error_message)
                messages = list(state["messages"])
                messages.append(ai_message)
                state["messages"] = messages
                state["is_done"] = True
                return state
    
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
    
    # 检查是否完成
    if action and action.strip().lower() == "final_answer":
        state["is_done"] = True
        
        # 确保生成最终回复
        if "answer" in action_input:
            answer_content = action_input["answer"]
            # 确保content是字符串格式
            if isinstance(answer_content, dict):
                answer_content = json.dumps(answer_content, ensure_ascii=False, indent=2)
            elif not isinstance(answer_content, str):
                answer_content = str(answer_content)
            ai_message = AIMessage(content=answer_content)
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
    
    # 确保response的content是字符串格式
    if hasattr(response, 'content'):
        content = response.content
        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False, indent=2)
        elif not isinstance(content, str):
            content = str(content)
        # 创建新的AIMessage确保content格式正确
        ai_message = AIMessage(content=content)
    else:
        ai_message = response
    
    # 更新状态
    return {
        **state,
        "messages": messages + [ai_message]
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

# 安全的代码执行沙箱 - 优化版本
def safe_code_executor(code: str, _locals: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """安全执行代码并返回结果和新变量 - 优化版本"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    logger.info(f"创建临时目录: {temp_dir}")
    
    try:
        # 存储执行前的变量键
        original_keys = set(_locals.keys())
        
        # 优化：只在需要时复制文件，避免大文件复制
        file_path = _locals.get("file_path")
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size_mb > 50:  # 大于50MB的文件不复制，直接使用原路径
                logger.info(f"大文件 {file_path} ({file_size_mb:.1f}MB)，使用原路径，不复制")
                # 在代码中注入文件路径变量
                code = f"# 文件路径变量\nfile_path = r'{file_path}'\n\n{code}"
            else:
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(temp_dir, file_name)
                shutil.copy2(file_path, dest_path)
                logger.info(f"复制文件 {file_path} 到 {dest_path}")
                # 在代码中注入文件路径变量
                code = f"# 文件路径变量\nfile_path = r'{dest_path}'\n\n{code}"
        
        # 写入代码到临时文件
        code_file = os.path.join(temp_dir, "code_to_execute.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)
        
        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        # 执行代码，优化超时设置
        try:
            process = subprocess.Popen(
                [sys.executable, code_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=temp_dir,
                env=env
            )
            
            # 根据文件大小调整超时时间
            timeout = 60 if file_path and os.path.getsize(file_path) > 10 * 1024 * 1024 else 30
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                execution_result = stdout
                if stderr:
                    execution_result += f"\n错误输出:\n{stderr}"
                
            except subprocess.TimeoutExpired:
                process.kill()
                execution_result = f"错误: 代码执行超时（{timeout}秒）"
                
        except Exception as e:
            execution_result = f"代码执行错误: {str(e)}"
    
        # 确定执行期间创建的新变量
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
        # 确保content是字符串格式
        if isinstance(answer, dict):
            answer_content = json.dumps(answer, ensure_ascii=False, indent=2)
        elif not isinstance(answer, str):
            answer_content = str(answer)
        else:
            answer_content = answer
            
        # 创建AI消息
        ai_message = AIMessage(content=answer_content)
        messages = list(state["messages"])
        messages.append(ai_message)
        state["messages"] = messages
        # 记录最终答案，便于前端直接读取
        state["final_answer"] = answer_content
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

def process_query(instruction: str, file_path: Optional[str] = None) -> Dict:
    """处理用户查询：理解需求→生成/执行代码→基于结果回答（ReAct 回路）"""
    # 检查网络连接
    if not check_network_connection():
        logger.warning("网络连接不稳定，但继续尝试处理请求")
    
    # 检查查询缓存
    cache_key = f"{instruction}_{file_path or 'no_file'}"
    if cache_key in _query_cache:
        logger.info(f"从缓存返回查询结果: {cache_key}")
        return _query_cache[cache_key]
    
    # 初始化对话消息
    messages: List[BaseMessage] = []

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
                f"文件路径: {file_path}\n\n"
                f"如果需要读取，请使用工具读取文件内容并进行分析。")
            messages.append(SystemMessage(content=system_message))
            logger.info(f"成功添加文件信息到系统消息: {file_name}")
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
        "max_iterations": 5,
        "action": None,
        "action_input": None,
        "observation": None,
        "is_done": False,
    }

    try:
        # 优化迭代式 ReAct 回路 - 减少不必要的循环
        max_iterations = state.get("max_iterations", 3)  # 减少默认迭代次数
        
        for iteration in range(max_iterations):
            # 1) 让 Agent 分析并给出"思考/行动/行动输入"
            state = react_agent_node(state)

            action_text = (state.get("action") or "").lower().strip()
            normalized_action = re.sub(r"[^a-z_]+", "", action_text)

            # 2) 根据行动执行
            if not action_text:
                continue

            # 2.1) 最终回答
            if (normalized_action == "final_answer") or ("final_answer" in action_text):
                state = final_answer_node(state)
                break

            # 2.2) 执行代码
            if ("执行代码" in action_text) or (normalized_action in ("execute_code", "generate_code")) or ("execute_code" in action_text) or ("generate_code" in action_text):
                action_input = state.get("action_input") or {}
                code = action_input.get("code") if isinstance(action_input, dict) else None
                if code:
                    state["code_to_execute"] = code
                    # 执行代码
                    state = execute_code_node(state)
                    
                    # 优化：如果执行成功，直接生成最终答案，避免额外迭代
                    execution_result = state.get("execution_result", "")
                    if execution_result and "错误" not in execution_result:
                        # 自动生成最终答案
                        final_answer = f"分析完成！\n\n执行结果：\n{execution_result}"
                        ai_message = AIMessage(content=final_answer)
                        messages = list(state["messages"])
                        messages.append(ai_message)
                        state["messages"] = messages
                        state["is_done"] = True
                        break
                    else:
                        # 执行失败，继续下一轮
                        observation_text = execution_result or "(无输出)"
                        state_messages = list(state["messages"])
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
        if ai_messages:
            last_content = ai_messages[-1].content
            # 确保content是字符串格式
            if isinstance(last_content, dict):
                response_text = json.dumps(last_content, ensure_ascii=False, indent=2)
            elif not isinstance(last_content, str):
                response_text = str(last_content)
            else:
                response_text = last_content
        else:
            response_text = f"收到指令：'{instruction}'。"

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
        result = {
            "response": final_answer_val or response_text,
            "code": state.get("code_to_execute"),
            "execution_result": state.get("execution_result"),
            "final_answer": final_answer_val,
            "intermediate_steps": intermediate_steps,
        }
        
        # 缓存结果
        _query_cache[cache_key] = result
        return result
    except Exception as e:
        logger.error(f"处理查询失败: {e}")
        
        # 如果是网络错误，提供备用处理方案
        if "Connection error" in str(e) or "网络" in str(e):
            return {
                "response": f"网络连接失败，请检查网络设置后重试。\n\n错误详情: {str(e)}\n\n建议:\n1. 检查网络连接\n2. 确认OpenAI API密钥有效\n3. 稍后重试",
                "code": None,
                "execution_result": None,
                "intermediate_steps": [],
            }
        else:
            return {
                "response": f"处理失败: {str(e)}",
                "code": None,
                "execution_result": None,
                "intermediate_steps": [],
            }