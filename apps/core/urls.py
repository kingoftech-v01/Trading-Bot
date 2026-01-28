"""
Core App URLs - API routing.

URL Namespaces:
- API: api:v1:core:resource-name
"""

from django.urls import path
from . import views_api

app_name = 'core'

urlpatterns = [
    path('health/', views_api.health_check, name='health-check'),
]
