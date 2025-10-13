"""
IDA Agent - 智能数据分析助手
使用 ReAct (思考-行动-执行) 方法解决数据分析问题

主要功能:
- 数据文件上传和分析
- 自动代码生成和执行
- 流式展示分析过程
- 聊天历史持久化
"""

import os
import logging
from typing import Dict, List, Optional, Any
import chainlit as cl
import aiofiles
from app.langgraph_workflow import process_query_streaming, detect_file_type

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 身份验证配置 ====================

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """
    密码验证回调函数
    根据 Chainlit 文档要求，需要这个函数来启用聊天历史功能
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        cl.User: 验证成功时返回用户对象
        None: 验证失败时返回 None
    """
    # 简单的用户名密码验证（生产环境中应该使用数据库和密码哈希）
    if (username, password) == ("admin", "ida2024"):
        return cl.User(
            identifier="admin", 
            metadata={"role": "admin", "provider": "credentials"}
        )
    elif (username, password) == ("user", "user123"):
        return cl.User(
            identifier="user", 
            metadata={"role": "user", "provider": "credentials"}
        )
    else:
        return None

# ==================== 聊天生命周期 ====================

@cl.on_chat_start
async def on_chat_start():
    """
    聊天会话开始时的初始化
    设置欢迎消息和会话状态
    """
    welcome_msg = """
# IDA Agent

我是一个智能数据分析助手，使用 **ReAct（思考-行动-执行）** 方法解决问题：

请告诉我您想要分析什么，或者上传一个文件开始吧！
    """

    await cl.Message(content=welcome_msg).send()

    # 初始化会话状态
    cl.user_session.set("file_path", None)
    logger.info("新的聊天会话已开始")

@cl.on_chat_resume
async def on_chat_resume(thread):
    """
    恢复聊天会话时的处理
    当用户点击历史对话时触发
    """
    logger.info(f"恢复聊天会话")
    
    # 从线程元数据中恢复文件路径 (如果有的话)
    try:
        if hasattr(thread, 'metadata') and thread.metadata:
            metadata = thread.metadata
            if "file_path" in metadata:
                file_path = metadata["file_path"]
                # 验证文件是否仍然存在
                if os.path.exists(file_path):
                    cl.user_session.set("file_path", file_path)
                    logger.info(f"恢复文件路径: {file_path}")
                else:
                    logger.warning(f"历史文件不存在: {file_path}")
                    cl.user_session.set("file_path", None)
    except Exception as e:
        logger.warning(f"恢复会话元数据时出错: {e}")
        cl.user_session.set("file_path", None)
    
    # 发送恢复消息
    resume_msg = f"📚 **会话已恢复**\n\n继续您的数据分析之旅..."
    await cl.Message(content=resume_msg).send()

# ==================== 步骤装饰器函数 ====================

@cl.step(name="思考", type="thinking")
async def thinking_step(thought_content: str):
    """
    显示AI的思考过程
    Args:
        thought_content: 思考内容文本
    Returns:
        思考内容
    """
    current_step = cl.context.current_step
    current_step.output = thought_content
    return thought_content

@cl.step(name="行动决策", type="action")
async def action_step(action: str, action_input: Dict = None):
    """
    显示AI的行动决策
    Args:
        action: 决策的行动类型
        action_input: 行动的输入参数
    Returns:
        格式化的行动内容
    """
    current_step = cl.context.current_step
    
    content = f"**决策:** {action}\n"
    
    # 如果是代码行动，显示代码内容
    if isinstance(action_input, dict) and "code" in action_input:
        content += f"\n**代码:**\n```python\n{action_input['code']}\n```"
        current_step.language = "python"
    elif isinstance(action_input, dict) and "answer" in action_input:
        # 如果是最终答案类型，显示答案内容
        content += f"\n**答案:** {action_input['answer']}"
    
    current_step.output = content
    return content

@cl.step(name="代码执行", type="code_execution")
async def code_execution_step(code: str):
    """
    显示代码执行步骤
    Args:
        code: 要执行的Python代码
    Returns:
        执行状态信息
    """
    current_step = cl.context.current_step
    current_step.input = code
    current_step.language = "python"
    
    # 流式显示执行状态
    await current_step.stream_token("⏳ 正在执行代码...\n\n")
    
    return "代码执行中..."

@cl.step(name="执行结果", type="result", show_input=False)
async def execution_result_step(result: str):
    """
    显示代码执行结果
    Args:
        result: 执行结果文本
    Returns:
        执行结果
    """
    current_step = cl.context.current_step
    current_step.output = result
    return result

@cl.step(name="观察", type="observation")
async def observation_step(content: str):
    """
    显示观察结果
    Args:
        content: 观察到的内容
    Returns:
        观察内容
    """
    current_step = cl.context.current_step
    current_step.output = content
    return content

# ==================== 主要消息处理函数 ====================

@cl.on_message
async def on_message(message: cl.Message):
    """
    处理用户消息的主函数
    支持文本输入和文件上传，使用ReAct方法进行分析
    
    Args:
        message: 用户发送的消息对象
    """
    # 验证消息有效性
    if not message or not hasattr(message, 'content'):
        logger.error("收到无效的消息对象")
        await cl.Message(content="❌ 收到无效消息，请重试").send()
        return
        
    user_input = message.content or ""
    file_path = cl.user_session.get("file_path")

    # 处理文件上传
    if message.elements:
        for element in message.elements:
            if isinstance(element, cl.File):
                try:
                    # 保存上传的文件
                    file_path = await save_uploaded_file(element)
                    cl.user_session.set("file_path", file_path)
                    
                    # 更新线程元数据以保存文件路径到聊天历史
                    await update_thread_metadata({"file_path": file_path})
                    
                    logger.info(f"文件上传成功: {element.name} -> {file_path}")
                except Exception as e:
                    error_msg = f"❌ 文件上传失败: {str(e)}"
                    await cl.Message(content=error_msg).send()
                    logger.error(f"文件上传处理失败: {e}")
                    return

    # 检查是否有用户输入
    if not user_input or user_input.strip() == "":
        logger.warning("没有用户输入内容")
        await cl.Message(content="请输入您的问题或需求。").send()
        return

    try:
        # 调用流式处理函数，实时嵌套步骤
        current_round_step = None
        current_round_num = None
        
        async for chunk in process_query_streaming(user_input, file_path, []):
            chunk_type = chunk.get("type")
            step_num = chunk.get("step", 0)
            
            if chunk_type == "step_start":
                # 如果是新的一轮，关闭之前的轮次步骤
                if current_round_step and hasattr(current_round_step, '__aexit__'):
                    await current_round_step.__aexit__(None, None, None)
                
                # 开始新的一轮分析步骤
                current_round_step = cl.Step(name=f"第 {step_num} 轮分析", type="round")
                await current_round_step.__aenter__()
                current_round_num = step_num
                
            elif chunk_type == "thought" and current_round_step:
                # 在当前轮次内显示思考过程
                thought_content = chunk.get("content", "")
                await thinking_step(thought_content)
                
            elif chunk_type == "action" and current_round_step:
                # 在当前轮次内显示行动决策
                action = chunk.get("action", "")
                action_input = chunk.get("action_input", {})
                if action and action.strip():
                    await action_step(action, action_input)
                    
            elif chunk_type == "code_execution_start" and current_round_step:
                # 在当前轮次内显示代码执行
                code = chunk.get("code", "")
                await code_execution_step(code)
                
            elif chunk_type == "code_execution_result" and current_round_step:
                # 在当前轮次内显示执行结果
                result = chunk.get("result", "")
                await execution_result_step(result)
                
            elif chunk_type == "observation" and current_round_step:
                # 在当前轮次内显示观察结果
                observation = chunk.get("content", "")
                await observation_step(observation)
                
            elif chunk_type in ["final_answer", "final_response"]:
                # 关闭最后的轮次步骤
                if current_round_step and hasattr(current_round_step, '__aexit__'):
                    await current_round_step.__aexit__(None, None, None)
                
                # 显示最终答案
                final_response = chunk.get("content", "")
                # await cl.Message(content=final_response).send()
                await send_message_with_images(final_response)
                break
                
            elif chunk_type == "error":
                # 关闭当前轮次步骤
                if current_round_step and hasattr(current_round_step, '__aexit__'):
                    await current_round_step.__aexit__(None, None, None)
                
                error_msg = chunk.get("message", "未知错误")
                await cl.Message(content=f"❌ **错误:** {error_msg}").send()
                return
        
        # 确保最后的步骤被正确关闭
        if current_round_step and hasattr(current_round_step, '__aexit__'):
            await current_round_step.__aexit__(None, None, None)

    except Exception as e:
        logger.error(f"处理消息时出错: {e}")
        await cl.Message(content=f"❌ **处理失败:** {str(e)}").send()
        return

# ==================== 辅助函数 ====================

async def update_thread_metadata(metadata: Dict[str, Any]):
    """
    更新当前线程的元数据
    用于保存状态信息到聊天历史
    
    Args:
        metadata: 要更新的元数据字典
    """
    try:
        thread = cl.context.session.thread
        if thread:
            current_metadata = thread.metadata or {}
            current_metadata.update(metadata)
            thread.metadata = current_metadata
            logger.info(f"更新线程元数据: {metadata}")
    except Exception as e:
        logger.error(f"更新线程元数据失败: {e}")

async def save_uploaded_file(file: cl.File) -> str:
    """
    保存上传的文件到本地data目录
    支持从file.path复制或file.content保存两种方式
    
    Args:
        file: Chainlit文件对象
        
    Returns:
        str: 保存后的本地文件路径
        
    Raises:
        ValueError: 文件内容为空或保存失败
    """
    logger.info(f"处理上传文件: {file.name}")
    logger.debug(f"文件对象类型: {type(file)}")
    logger.debug(f"文件对象属性: {[attr for attr in dir(file) if not attr.startswith('_')]}")
    
    # 在新版本的Chainlit中，文件已经被保存到临时目录
    # 我们需要检查file.path属性
    if hasattr(file, 'path') and file.path:
        source_path = file.path
        logger.info(f"找到文件路径: {source_path}")
        
        # 检查文件是否存在
        if not os.path.exists(source_path):
            logger.error(f"源文件不存在: {source_path}")
            raise ValueError(f"文件 '{file.name}' 的源路径不存在")
        
        # 检查文件大小
        source_size = os.path.getsize(source_path)
        logger.info(f"源文件大小: {source_size} 字节")
        
        if source_size == 0:
            logger.error(f"文件大小为0: {file.name}")
            raise ValueError(f"文件 '{file.name}' 大小为0字节，请确保文件包含数据")
        
        # 确保 data 目录存在
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)

        # 生成唯一文件名
        import time
        timestamp = int(time.time())
        name, ext = os.path.splitext(file.name)
        safe_name = f"{name}_{timestamp}{ext}"
        dest_path = os.path.join(data_dir, safe_name)

        try:
            # 复制文件到目标目录
            import shutil
            shutil.copy2(source_path, dest_path)
            
            # 验证复制是否成功
            if not os.path.exists(dest_path):
                raise ValueError(f"文件复制失败，目标路径不存在: {dest_path}")
                
            dest_size = os.path.getsize(dest_path)
            if dest_size != source_size:
                raise ValueError(f"文件复制不完整，源文件: {source_size} 字节，目标文件: {dest_size} 字节")
            
            logger.info(f"文件已成功保存: {dest_path} (大小: {dest_size} 字节)")
            return dest_path
            
        except Exception as e:
            logger.error(f"文件复制失败: {e}")
            # 清理可能创建的不完整文件
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except:
                    pass
            raise e
    
    # 回退到旧方法（兼容旧版本）
    elif hasattr(file, 'content') and file.content is not None:
        content = file.content
        logger.info(f"使用file.content，大小: {len(content)} 字节")
        
        if len(content) == 0:
            raise ValueError(f"文件 '{file.name}' 内容为空")
        
        # 确保 data 目录存在
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)

        # 生成唯一文件名
        import time
        timestamp = int(time.time())
        name, ext = os.path.splitext(file.name)
        safe_name = f"{name}_{timestamp}{ext}"
        dest_path = os.path.join(data_dir, safe_name)

        try:
            # 保存文件内容
            async with aiofiles.open(dest_path, 'wb') as f:
                await f.write(content)
            
            logger.info(f"文件已保存: {dest_path} (大小: {len(content)} 字节)")
            return dest_path
            
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except:
                    pass
            raise e
    
    else:
        logger.error(f"无法获取文件内容，文件对象缺少path和content属性")
        raise ValueError(f"文件 '{file.name}' 无法访问，请检查Chainlit配置或尝试重新上传")

async def send_message_with_images(finalResponse: str) -> bool:
    """
    用于前端显示的文本处理。
    该函数会解析包含Markdown图片格式的字符串，
    并将其拆分为文本和图片消息，然后交错发送至前端，
    以实现"文字-图片-文字-图片"的显示效果。

    :param finalResponse: 包含Markdown图片链接的字符串。
    :return: bool, 表示是否发送成功。
    """
    try:
        # 用于匹配Markdown图片语法 ![alt text](path) 的正则表达式
        # (.*?) 是一个非贪婪捕获组，用于提取括号内的图片路径
        pattern = r'!\[.*?\]\((.*?)\)'

        # 使用正则表达式分割字符串。
        # 分割后会得到一个列表，其中偶数索引为文本，奇数索引为图片路径
        # 例如: "text1 ![img](./cat.jpeg) text2" -> ['text1 ', './cat.jpeg', ' text2']
        parts = re.split(pattern, finalResponse)

        # 遍历分割后的部分
        for i, part in enumerate(parts):
            # 索引为偶数的是文本部分
            if i % 2 == 0:
                # 如果文本部分不为空白，则发送文本消息
                if part and part.strip():
                    await cl.Message(content=part.strip()).send()
            # 索引为奇数的是图片路径
            else:
                image_path = part.strip()
                # 检查图片文件是否存在
                if os.path.exists(image_path):
                    # 提取文件名作为图片的name
                    image_name = os.path.basename(image_path)
                    
                    # 创建图片元素
                    image = cl.Image(path=image_path, name=image_name, display="inline")
                    
                    # 发送图片消息，可以附带空文本
                    await cl.Message(
                        content="",  # 发送空内容以避免多余的文本
                        elements=[image],
                    ).send()
                else:
                    # 如果图片不存在，可以发送一条错误提示
                    # debug
                    error_msg = f"--- 图片未找到: {image_path} ---"
                    await cl.Message(content=error_msg).send()
        
        return True

    except Exception as e:
        logger.error(f"发送图文混合消息失败: {e}")
        return False
        
# ==================== 程序入口点 ====================

if __name__ == "__main__":
    """
    程序入口点
    开发模式下可以直接运行此文件启动Chainlit应用
    """
    import subprocess
    import sys
    
    try:
        logger.info("启动 IDA Agent Chainlit 应用...")
        
        # 检查并安装依赖
        logger.info("检查依赖包...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True)
        
        # 启动Chainlit应用
        logger.info("启动Chainlit服务器...")
        subprocess.run([
            "chainlit", "run", "chainlit_app.py", 
            "--host", "0.0.0.0", 
            "--port", "8080"
        ])
        
    except Exception as e:
        logger.error(f"启动应用失败: {e}")
        sys.exit(1)