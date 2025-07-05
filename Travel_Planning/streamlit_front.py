# streamlit_front.py

import streamlit as st
import asyncio
from config import TravelAgent
import logging

# 设置页面配置
st.set_page_config(
    page_title="智能旅行规划助手",
    page_icon="✈️",
    layout="wide",
)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.travel_agent = None

# 标题和简介
st.title("🚄 智能旅行规划助手")
st.markdown("""
欢迎使用智能旅行规划助手！我可以帮助您：
- 查询高铁票务信息
- 规划市内公交地铁路线
- 提供完整的出行方案
""")


# 清除聊天历史函数
def clear_chat_history():
    st.session_state.messages = []
    st.session_state.travel_agent = None


# 添加清除聊天按钮
if st.session_state.messages:
    if st.button("🧹 清除聊天记录"):
        clear_chat_history()
        st.rerun()

# 侧边栏信息
with st.sidebar:
    st.header("关于")
    st.markdown("""
    ### 功能说明
    本系统整合了高德地图API和12306票务数据，为您提供一站式旅行规划服务。

    ### 使用提示
    1. 请尽量详细描述您的需求
    2. 包含出发地、目的地、日期等信息
    3. 可以指定交通偏好（如只坐高铁）
    """)
    st.markdown("---")
    st.markdown("© 2025 智能旅行规划系统 | 端口:8003")


# 初始化旅行代理
async def init_agent():
    if st.session_state.travel_agent is None:
        st.session_state.travel_agent = TravelAgent()
        with st.spinner("正在初始化旅行规划引擎..."):
            await st.session_state.travel_agent.initialize()


# 处理用户输入并显示流式响应
async def handle_user_input(user_input: str):
    # 添加到聊天历史
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(user_input)

    # 显示助手响应
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            async for chunk in st.session_state.travel_agent.process_query(user_input):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            error_msg = f"抱歉，处理请求时出错: {str(e)}"
            response_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})


# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入表单
with st.form(key="user_input_form"):
    user_input = st.text_area(
        "请输入您的旅行需求:",
        placeholder="例如: 查询上海东方明珠景点到上海迪士尼乐园的的驾车路线规划",
        height=100,
        key="user_input"
    )

    submit_button = st.form_submit_button("提交")

    if submit_button and user_input.strip():
        asyncio.run(init_agent())
        asyncio.run(handle_user_input(user_input))
        st.rerun()

# 运行Streamlit应用
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )