"""
Indicators App URLs - API routing.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api

router = DefaultRouter()
router.register(r'types', views_api.IndicatorTypeViewSet, basename='indicator-type')
router.register(r'configs', views_api.IndicatorConfigViewSet, basename='indicator-config')
router.register(r'results', views_api.IndicatorResultViewSet, basename='indicator-result')

app_name = 'indicators'

urlpatterns = [
    path('', include(router.urls)),
    path('calculate/', views_api.CalculateIndicatorsAPIView.as_view(), name='calculate'),
]
