"""
URL configuration for the signals app.

Following URL_AND_VIEW_CONVENTIONS.md:
- Frontend URLs: /signals/...
- API URLs: /api/v1/signals/...
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_api import (
    VoteViewSet,
    SignalSessionViewSet,
    SignalViewSet,
    ConfluenceScoreViewSet,
    GenerateSignalAPIView,
    VotingStatusAPIView,
)
from .views_frontend import (
    SignalListView,
    SignalDetailView,
    ActiveSignalsView,
    SignalSessionListView,
    SignalSessionDetailView,
    GenerateSignalView,
    VotingStatusView,
    SignalDashboardView,
)


# API Router
router = DefaultRouter()
router.register(r'votes', VoteViewSet, basename='vote')
router.register(r'sessions', SignalSessionViewSet, basename='session')
router.register(r'signals', SignalViewSet, basename='signal')
router.register(r'confluence', ConfluenceScoreViewSet, basename='confluence')


# API URL patterns
# Namespace: api:v1:signals
api_urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Custom API endpoints
    path('generate/', GenerateSignalAPIView.as_view(), name='generate'),
    path('voting-status/', VotingStatusAPIView.as_view(), name='voting-status'),
]


# Frontend URL patterns
# Namespace: frontend:signals
frontend_urlpatterns = [
    # Dashboard
    path('', SignalDashboardView.as_view(), name='dashboard'),
    path('dashboard/', SignalDashboardView.as_view(), name='dashboard_alt'),

    # Signals
    path('list/', SignalListView.as_view(), name='signal_list'),
    path('active/', ActiveSignalsView.as_view(), name='signal_active'),
    path('<uuid:pk>/', SignalDetailView.as_view(), name='signal_detail'),

    # Sessions
    path('sessions/', SignalSessionListView.as_view(), name='session_list'),
    path('sessions/<uuid:pk>/', SignalSessionDetailView.as_view(), name='session_detail'),

    # Generate
    path('generate/', GenerateSignalView.as_view(), name='generate'),

    # Voting Status
    path('voting-status/', VotingStatusView.as_view(), name='voting_status'),
]


# Combined patterns for app inclusion
urlpatterns = frontend_urlpatterns
