"""
Indicators App Frontend URLs - HTML routing.
"""

from django.urls import path
from . import views_frontend

app_name = 'indicators'

urlpatterns = [
    path('', views_frontend.indicator_dashboard, name='dashboard'),
    path('list/', views_frontend.indicator_list, name='indicator_list'),
    path('<uuid:pk>/', views_frontend.indicator_detail, name='indicator_detail'),
]
