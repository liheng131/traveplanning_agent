# backend/api/views.py

from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt # <-- 1. 导入 csrf_exempt
import asyncio
import json
from config.agent_workflow import TravelAgent

# ------------------------------------------------------------------
# Agent 初始化逻辑保持不变
# ...
travel_agent_instance = TravelAgent()
agent_initialized = asyncio.Event()

async def initialize_agent():
    """异步初始化 Agent"""
    if not agent_initialized.is_set():
        print("Initializing TravelAgent...")
        await travel_agent_instance.initialize()
        agent_initialized.set()
        print("TravelAgent initialized.")

if not agent_initialized.is_set():
    asyncio.run(initialize_agent())
# ------------------------------------------------------------------


@csrf_exempt # <-- 2. 在视图函数正上方添加这个装饰器
async def plan_travel_view(request):
    """
    处理旅行规划请求的纯 Django 异步视图
    """
    # ... 函数的其余部分保持不变 ...
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST method is allowed"}, status=405)

    try:
        data = json.loads(request.body)
        query = data.get('query')
        if not query:
            return JsonResponse({"error": "Query not provided in request body"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)

    await agent_initialized.wait()

    async def stream_response_generator():
        try:
            async for chunk in travel_agent_instance.process_query(query):
                yield chunk.encode('utf-8')
        except Exception as e:
            print(f"Error during agent processing: {e}")
            error_message = f"处理请求时发生错误: {e}"
            yield error_message.encode('utf-8')

    return StreamingHttpResponse(stream_response_generator(), content_type="text/plain; charset=utf-8")