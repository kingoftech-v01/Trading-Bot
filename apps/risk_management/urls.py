"""
URL configuration for the risk_management app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_api import (
    RiskProfileViewSet,
    PositionSizeCalculationViewSet,
    DailyRiskTrackerViewSet,
    CalculatePositionSizeAPIView,
    RiskSummaryAPIView,
)
from .views_frontend import (
    RiskProfileListView,
    RiskProfileDetailView,
    RiskProfileCreateView,
    RiskProfileUpdateView,
    CalculatorView,
    RiskDashboardView,
)


# API Router
router = DefaultRouter()
router.register(r'profiles', RiskProfileViewSet, basename='profile')
router.register(r'calculations', PositionSizeCalculationViewSet, basename='calculation')
router.register(r'daily-trackers', DailyRiskTrackerViewSet, basename='daily-tracker')


# API URL patterns
api_urlpatterns = [
    path('', include(router.urls)),
    path('calculate/', CalculatePositionSizeAPIView.as_view(), name='calculate'),
    path('summary/', RiskSummaryAPIView.as_view(), name='summary'),
]


# Frontend URL patterns
frontend_urlpatterns = [
    path('', RiskDashboardView.as_view(), name='dashboard'),
    path('profiles/', RiskProfileListView.as_view(), name='profile_list'),
    path('profiles/create/', RiskProfileCreateView.as_view(), name='profile_create'),
    path('profiles/<uuid:pk>/', RiskProfileDetailView.as_view(), name='profile_detail'),
    path('profiles/<uuid:pk>/edit/', RiskProfileUpdateView.as_view(), name='profile_update'),
    path('calculator/', CalculatorView.as_view(), name='calculator'),
]


urlpatterns = frontend_urlpatterns
