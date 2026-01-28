"""
Core Frontend Views - Base views for HTML template rendering.

This module provides base view classes and utilities for frontend views.
Following URL_AND_VIEW_CONVENTIONS.md for frontend layer.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    """
    Core index view - redirects to dashboard.

    Template: core/index.html
    """
    return render(request, 'core/index.html', {
        'page_title': 'Trading Bot',
    })
