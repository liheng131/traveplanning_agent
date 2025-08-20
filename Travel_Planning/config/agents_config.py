# agents_config.py

import os
from typing import Literal
from langchain.schema import AIMessage
import re
from typing import List, Any, Dict
import json
import aiofiles
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage


async def load_single_mcp_config(key: str, file_path: str = "servers_config.json") -> str:
    """加载配置文件，解析环境变量，并返回指定 key 的完整项（包含 key），以 JSON 字符串格式返回"""

    load_dotenv()  # 加载 .env 文件中的环境变量

    def resolve_env_vars(config: Any) -> Any:
        if isinstance(config, dict):
            return {k: resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [resolve_env_vars(i) for i in config]
        #
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            var_name = config[2:-1]
            return os.environ.get(var_name, "")
        else:
            return config

    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
        content = await f.read()
        config = json.loads(content)
        config = resolve_env_vars(config)
        selected = config.get("mcpServers", {}).get(key)
        result = {key: selected} if selected else {}
        res = json.loads(json.dumps(result, indent=2, ensure_ascii=False))
        return res


async def parse_messages(messages: List[Any]) -> str:
    """
    解析消息列表，返回包含 HumanMessage、AIMessage 和 ToolMessage 的详细信息的字符串

    Args:
        messages: 包含消息的列表，每个消息是一个对象

    Returns:
        包含所有消息解析结果的字符串
    """
    output = []
    output.append("=== 消息解析结果 ===")
    for idx, msg in enumerate(messages, 1):
        msg_output = []
        msg_output.append(f"\n消息 {idx}:")
        # 获取消息类型
        msg_type = msg.__class__.__name__
        msg_output.append(f"类型: {msg_type}")

        # 角色识别
        if msg_type == 'HumanMessage':
            msg_output.append("角色：用户")
        elif msg_type == 'AIMessage':
            name = getattr(msg, 'name', '代理')
            msg_output.append(f"角色：{name}代理")

        # 提取消息内容
        content = getattr(msg, 'content', '')
        msg_output.append(f"内容: {content if content else '<空>'}")

        # 处理附加信息
        additional_kwargs = getattr(msg, 'additional_kwargs', {})
        if additional_kwargs:
            msg_output.append("附加信息:")
            for key, value in additional_kwargs.items():
                if key == 'tool_calls' and value:
                    msg_output.append("  工具调用:")
                    for tool_call in value:
                        msg_output.append(f"    - ID: {tool_call['id']}")
                        msg_output.append(f"      函数: {tool_call['function']['name']}")
                        msg_output.append(f"      参数: {tool_call['function']['arguments']}")
                else:
                    msg_output.append(f"  {key}: {value}")

        # 处理 ToolMessage 特有字段
        if msg_type == 'ToolMessage':
            tool_name = getattr(msg, 'name', '')
            tool_call_id = getattr(msg, 'tool_call_id', '')
            msg_output.append(f"工具名称: {tool_name}")
            msg_output.append(f"工具调用 ID: {tool_call_id}")

        # 处理 AIMessage 的工具调用和元数据
        if msg_type == 'AIMessage':
            tool_calls = getattr(msg, 'tool_calls', [])
            if tool_calls:
                msg_output.append("工具调用:")
                for tool_call in tool_calls:
                    msg_output.append(f"  - 名称: {tool_call['name']}")
                    msg_output.append(f"    参数: {tool_call['args']}")
                    msg_output.append(f"    ID: {tool_call['id']}")

            # 提取元数据
            metadata = getattr(msg, 'response_metadata', {})
            if metadata:
                msg_output.append("元数据:")
                token_usage = metadata.get('token_usage', {})
                msg_output.append(f"  令牌使用: {token_usage}")
                msg_output.append(f"  模型名称: {metadata.get('model_name', '未知')}")
                msg_output.append(f"  完成原因: {metadata.get('finish_reason', '未知')}")

        # 添加消息 ID
        msg_id = getattr(msg, 'id', '未知')
        msg_output.append(f"消息 ID: {msg_id}")
        msg_output.append("-" * 50)

        output.append("\n".join(msg_output))

    return "\n".join(output)


def deduplicate_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    对消息列表进行去重处理，基于消息的类型、内容、name和additional_kwargs

    参数:
        messages: 待去重的消息列表

    返回:
        去重后的消息列表
    """
    if not messages:
        return messages

    unique_messages = []
    seen = set()

    for msg in messages:
        # 创建消息的唯一标识（包含类型、内容、name和additional_kwargs）
        msg_identifier = (
            msg.__class__.__name__,
            msg.content,
            getattr(msg, 'name', None),
            frozenset(getattr(msg, 'additional_kwargs', {}).items())
        )

        if msg_identifier not in seen:
            seen.add(msg_identifier)
            unique_messages.append(msg)

    return unique_messages


async def list_and_return_tools(client):
    """
    获取所有可用工具信息，返回工具列表和格式化字符串

    Args:
        client: 客户端对象，用于获取工具列表

    Returns:
        tuple: (工具列表, 格式化字符串)
    """
    tools = await client.get_tools()
    output_lines = []
    valid_tools = []
    # 构建工具信息字符串
    # output_lines.append("────────────────────")
    for i, tool in enumerate(tools, 1):
        if isinstance(tool, str):
            # 如果是字符串，打印一个警告，并跳过这个错误的元素
            print(f"警告：工具列表中发现一个无效的字符串元素 '{tool}'，已自动忽略。请检查后台服务或客户端配置。")
            continue  # 跳过当前循环的剩余部分
        valid_tools.append(tool)  # 将有效的工具添加到新列表中
        output_lines.append(f"\n{i}. {tool.name.upper()}")
        output_lines.append(f"   {tool.description}")

        if hasattr(tool, 'args_schema') and 'properties' in tool.args_schema:
            output_lines.append("   Parameters:")
            for param, details in tool.args_schema['properties'].items():
                required = "(必填)" if param in tool.args_schema.get('required', []) else ""
                output_lines.append(
                    f"    - {param}: {details.get('type', '')} {details.get('description', '')} {required}"
                )
        # output_lines.append("────────────────────")

    # 将列表合并为字符串
    tools_info = "\n".join(output_lines)

    return valid_tools, tools_info  # 返回工具列表和格式化字符串


async def keep_last_message(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    保留 state 中所有字段及其原始顺序，但将 messages 列表仅保留最后一个元素。

    参数:
        state: 包含 messages 列表的字典

    返回:
        新字典，保持原始字段顺序，messages 仅包含最后一个元素
    """
    # 创建新字典，保持原始顺序
    new_state = {}

    # 按原始顺序处理所有字段
    for key, value in state.items():
        if key == 'messages':
            # 处理 messages 字段
            if isinstance(value, list) and len(value) > 0:
                new_state[key] = [value[-1]]  # 仅保留最后一个元素
            else:
                new_state[key] = []  # 如果没有消息或 messages 不是列表，设为空列表
        else:
            # 其他字段保持不变
            new_state[key] = value

    return new_state


async def agent_node(state, agent, name):
    # 调用代理
    if name == "supervisor":
        agent_response = await agent.ainvoke(state)

    else:
        new_state = await keep_last_message(state)
        agent_response = await agent.ainvoke(new_state)

    # agent_response = await agent.ainvoke(state)

    agent_response_content = agent_response['messages'][-1].content

    return {
        "messages": [AIMessage(content=str(agent_response_content), name=name)],
        "sender": [name],
    }


async def supervisor_router(state) -> Literal["navigation_expert", "ticketing_expert", "__end__"]:
    messages = state["messages"]
    if not messages:
        return "__end__"  # 空消息直接终止

    last_message = messages[-1]

    # 内容提取与清洗
    content = last_message.content.strip() if hasattr(last_message, 'content') else ""
    if not content:
        return "__end__"

    # 提取末行指令（兼容多行和单行情况）
    last_line = content.splitlines()[-1].strip().lower()

    # 指令正则匹配（严格模式）
    final_answer_pattern = r'^final\s+answer$'
    nav_pattern = r'^navigation_expert$'
    ticket_pattern = r'^ticketing_expert$'

    # 优先级判定
    if re.match(final_answer_pattern, last_line):
        return "__end__"
    elif re.match(nav_pattern, last_line):
        # 循环调用保护（示例阈值3次）
        nav_calls = sum(1 for msg in messages if 'navigation_expert' in getattr(msg, 'content', ''))
        return "navigation_expert" if nav_calls < 7 else "__end__"
    elif re.match(ticket_pattern, last_line):
        # 循环调用保护
        ticket_calls = sum(1 for msg in messages if 'ticketing_expert' in getattr(msg, 'content', ''))
        return "ticketing_expert" if ticket_calls < 7 else "__end__"

    # 模糊决策（根据提示词建议优先导航）
    if any(keyword in content.lower() for keyword in ["路线", "导航", "位置", "map"]):
        return "navigation_expert"
    elif any(keyword in content.lower() for keyword in ["票务", "购票", "ticket"]):
        return "ticketing_expert"

    # 默认安全终止
    return "__end__"


def save_graph_visualization(graph, filename: str = "graph_app.png") -> None:
    """保存状态图的可视化表示。

    Args:
        graph: 状态图实例。
        filename: 保存文件路径。
    """
    # 尝试执行以下代码块
    try:
        # 以二进制写模式打开文件
        with open(filename, "wb") as f:
            # 将状态图转换为Mermaid格式的PNG并写入文件
            f.write(graph.get_graph().draw_mermaid_png())
        # 记录保存成功的日志
        print(f"Graph visualization saved as {filename}")
    # 捕获IO错误
    except IOError as e:
        # 记录警告日志
        print(f"Failed to save graph visualization: {e}")
