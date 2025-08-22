# backend/api/views.py

from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import asyncio
import json
from config.agent_workflow import TravelAgent

# ------------------------------------------------------------------
# Agent 初始化逻辑
# ------------------------------------------------------------------
# 1. 在全局范围创建 Agent 实例和事件标志
travel_agent_instance = TravelAgent()
agent_initialized = asyncio.Event()


async def initialize_agent():
    """异步初始化 Agent，并设置事件标志"""
    # 这个 if 语句可以防止在并发请求下被重复执行
    if not agent_initialized.is_set():
        print("Initializing TravelAgent for the first time...")
        try:
            # 这一步会启动 npx 进程并打印日志
            await travel_agent_instance.initialize()
            agent_initialized.set()  # 设置标志，表示初始化已完成
            print("TravelAgent initialized and ready.")
        except Exception as e:
            print(f"FATAL: Agent initialization failed: {e}")


# 2. 确保这里没有任何 asyncio.run(...) 的调用！
# ------------------------------------------------------------------


@csrf_exempt
async def plan_travel_view(request):
    """
    处理旅行规划请求的视图
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST method is allowed"}, status=405)

    # 3. 在处理请求前，检查并等待初始化完成
    # 这个逻辑确保了初始化只在第一个请求时执行一次。
    if not agent_initialized.is_set():
        await initialize_agent()

    try:
        data = json.loads(request.body)
        query = data.get('query')
        if not query:
            return JsonResponse({"error": "Query not provided in request body"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)

    async def stream_response_generator():
        try:
            async for chunk in travel_agent_instance.process_query(query):
                yield chunk.encode('utf-8')
        except Exception as e:
            import traceback
            print("Error during agent processing:")
            traceback.print_exc()
            error_message = f"抱歉，处理您的请求时发生内部错误。"
            yield error_message.encode('utf-8')

    return StreamingHttpResponse(stream_response_generator(), content_type="text/plain; charset=utf-8")