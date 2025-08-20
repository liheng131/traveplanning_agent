# backend/api/urls.py

from django.urls import path
from .views import plan_travel_view # <-- 从 views 导入函数，而不是类

urlpatterns = [
    # 直接使用函数视图，不再需要 .as_view()
    path('plan/', plan_travel_view, name='plan-travel'),
]