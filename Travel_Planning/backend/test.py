import asyncio
from Travel_Planning.backend.config import TravelAgent


async def main():
    process_query = "我现在在湖南长沙，需要去黄山，给我推荐一下怎么去以及旅游方案"
    t = TravelAgent()
    # await t.initialize()  # 初始化
    # response = await t.process_query(process_query)
    # print(response)
    async for response in t.process_query(process_query):  # 遍历异步生成器
        print(response)  # 处理每个返回的结果


if __name__ == "__main__":
    asyncio.run(main())
