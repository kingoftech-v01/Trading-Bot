"""
Core App Frontend URLs - HTML routing.

URL Namespaces:
- Frontend: frontend:core:view_name
"""

from django.urls import path
from . import views_frontend

app_name = 'core'

urlpatterns = [
    path('', views_frontend.index, name='index'),
]
