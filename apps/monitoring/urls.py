"""URL configuration for the monitoring app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_api import (
    AlertViewSet, HealthCheckViewSet, ReportViewSet,
    HealthAPIView, GenerateReportAPIView,
)
from .views_frontend import (
    AlertListView, AlertDetailView,
    ReportListView, ReportDetailView,
    MonitoringDashboardView, SystemDashboardView,
)

router = DefaultRouter()
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'health-checks', HealthCheckViewSet, basename='health-check')
router.register(r'reports', ReportViewSet, basename='report')

api_urlpatterns = [
    path('', include(router.urls)),
    path('health/', HealthAPIView.as_view(), name='health'),
    path('generate-report/', GenerateReportAPIView.as_view(), name='generate-report'),
]

frontend_urlpatterns = [
    path('', MonitoringDashboardView.as_view(), name='dashboard'),
    path('system/', SystemDashboardView.as_view(), name='system_dashboard'),
    path('alerts/', AlertListView.as_view(), name='alert_list'),
    path('alerts/<uuid:pk>/', AlertDetailView.as_view(), name='alert_detail'),
    path('reports/', ReportListView.as_view(), name='report_list'),
    path('reports/<uuid:pk>/', ReportDetailView.as_view(), name='report_detail'),
]

urlpatterns = frontend_urlpatterns
