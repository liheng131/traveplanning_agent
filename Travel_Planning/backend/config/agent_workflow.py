# agent_workflow.py

from langgraph.graph import END, StateGraph, START
import functools
from langchain.schema import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.chat_models import init_chat_model
# from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import AsyncGenerator
from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langchain_community.llms import Tongyi
from .agents_config import (
    agent_node, supervisor_router,
    list_and_return_tools, load_single_mcp_config,
    parse_messages
)
from .promptstemp import (
    navigation_prompt, ticketing_prompt,
    supervisor_prompt, system_prompt_template,
    question_prompt_template
)
import operator
from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import BaseMessage

load_dotenv(override=True)


class AgentState(TypedDict):
    # messages字段用于存储消息的序列，并且通过 Annotated 和 operator.add 提供了额外的信息，解释如何处理这些消息。
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # sender 用于存储当前消息的发送者。通过这个字段，系统可以知道当前消息是由哪个代理生成的。
    sender: Annotated[List[str], operator.add]


class TravelAgent:
    def __init__(self):
        self.app = None  # 图应用
        self.output_model = ChatTongyi(model='qwen-turbo-latest')
        self.final_prompt = ChatPromptTemplate.from_messages([
            ('system', system_prompt_template),
            ('human', question_prompt_template)
        ])

    async def initialize(self):
        """初始化代理和工作流"""
        # 进入
        client_map = MultiServerMCPClient(await load_single_mcp_config("amap-maps"))
        client_mcp = MultiServerMCPClient(await load_single_mcp_config("12306-mcp"))

        tools_map, tools_map_info = await list_and_return_tools(client_map)
        tools_mcp, tools_mcp_info = await list_and_return_tools(client_mcp)

        # 创建各个专家代理
        agent_map = create_react_agent(
            model=self.output_model,
            name="navigation_expert",
            tools=tools_map,
            prompt=SystemMessage(content=(navigation_prompt(tools_map_info)))
        )

        agent_mcp = create_react_agent(
            model=self.output_model,
            name="ticketing_expert",
            tools=tools_mcp,
            prompt=SystemMessage(content=(ticketing_prompt(tools_mcp_info)))
        )

        supervisor = create_react_agent(
            tools=[],
            model=self.output_model,
            name="supervisor",
            prompt=SystemMessage(content=supervisor_prompt()),
        )

        # 创建工作流
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("supervisor", functools.partial(agent_node, agent=supervisor, name="supervisor"))
        workflow.add_node("navigation_expert", functools.partial(agent_node, agent=agent_map, name="navigation_expert"))
        workflow.add_node("ticketing_expert", functools.partial(agent_node, agent=agent_mcp, name="ticketing_expert"))

        # 添加边
        workflow.add_conditional_edges(
            "supervisor",
            supervisor_router,
            {
                "navigation_expert": "navigation_expert",
                "ticketing_expert": "ticketing_expert",
                "__end__": END
            }
        )
        workflow.add_edge("navigation_expert", "supervisor")
        workflow.add_edge("ticketing_expert", "supervisor")
        workflow.add_edge(START, "supervisor")

        self.app = workflow.compile(name="travel_agent")

    async def process_query(self, query: str) -> AsyncGenerator[str, None]:
        """处理用户查询并返回流式响应"""
        if not self.app:
            await self.initialize()

        # 第一步：获取原始响应
        agent_response = await self.app.ainvoke(
            {"messages": [HumanMessage(content=query)]}
        )
        print(agent_response)
        formatted_response = await parse_messages(agent_response['messages'])
        # print("_________1_______")
        # print(formatted_response)
        # print("_________2_______")
        # print("以上是原始响应")

        # 第二步：使用大模型生成最终响应
        chain = self.final_prompt | self.output_model
        async for chunk in chain.astream({
            "query": query,
            "context": formatted_response
        }):
            yield chunk.content
