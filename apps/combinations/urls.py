"""
URL configuration for the combinations app.

Following URL_AND_VIEW_CONVENTIONS.md:
- Frontend URLs: /combinations/...
- API URLs: /api/v1/combinations/...
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_api import (
    CombinationViewSet,
    CombinationResultViewSet,
    EvaluateCombinationAPIView,
    EvaluateAllCombinationsAPIView,
    CombinationInfoAPIView,
)
from .views_frontend import (
    CombinationListView,
    CombinationDetailView,
    CombinationCreateView,
    CombinationUpdateView,
    CombinationDeleteView,
    CombinationResultListView,
    CombinationResultDetailView,
    EvaluateCombinationsView,
    CombinationInfoView,
)


# API Router
router = DefaultRouter()
router.register(r'combinations', CombinationViewSet, basename='combination')
router.register(r'results', CombinationResultViewSet, basename='result')


# API URL patterns
# Namespace: api:v1:combinations
api_urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Custom API endpoints
    path('evaluate/', EvaluateCombinationAPIView.as_view(), name='evaluate'),
    path('evaluate-all/', EvaluateAllCombinationsAPIView.as_view(), name='evaluate-all'),
    path('info/', CombinationInfoAPIView.as_view(), name='info'),
]


# Frontend URL patterns
# Namespace: frontend:combinations
frontend_urlpatterns = [
    # Combination CRUD
    path('', CombinationListView.as_view(), name='combination_list'),
    path('create/', CombinationCreateView.as_view(), name='combination_create'),
    path('<uuid:pk>/', CombinationDetailView.as_view(), name='combination_detail'),
    path('<uuid:pk>/edit/', CombinationUpdateView.as_view(), name='combination_update'),
    path('<uuid:pk>/delete/', CombinationDeleteView.as_view(), name='combination_delete'),

    # Results
    path('results/', CombinationResultListView.as_view(), name='result_list'),
    path('results/<uuid:pk>/', CombinationResultDetailView.as_view(), name='result_detail'),

    # Evaluation
    path('evaluate/', EvaluateCombinationsView.as_view(), name='evaluate'),

    # Info
    path('info/', CombinationInfoView.as_view(), name='info'),
]


# Combined patterns for app inclusion
urlpatterns = frontend_urlpatterns
