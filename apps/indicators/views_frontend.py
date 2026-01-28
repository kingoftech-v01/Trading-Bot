"""
Indicators Frontend Views - HTML template views.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import IndicatorType, IndicatorConfig, IndicatorResult


@login_required
def indicator_list(request):
    """List all indicator types."""
    indicators = IndicatorType.objects.filter(is_active=True)
    return render(request, 'indicators/indicator_list.html', {
        'indicators': indicators,
        'page_title': 'Technical Indicators',
    })


@login_required
def indicator_detail(request, pk):
    """Show indicator details and configuration."""
    indicator = get_object_or_404(IndicatorType, pk=pk, is_active=True)
    configs = indicator.configs.filter(is_enabled=True).select_related('trading_pair')

    return render(request, 'indicators/indicator_detail.html', {
        'indicator': indicator,
        'configs': configs,
        'page_title': indicator.display_name,
    })


@login_required
def indicator_dashboard(request):
    """Indicator analysis dashboard."""
    indicator_types = IndicatorType.objects.filter(is_active=True)
    recent_results = IndicatorResult.objects.select_related(
        'config__indicator_type',
        'config__trading_pair'
    ).order_by('-timestamp')[:20]

    return render(request, 'indicators/dashboard.html', {
        'indicator_types': indicator_types,
        'recent_results': recent_results,
        'page_title': 'Indicator Dashboard',
    })
