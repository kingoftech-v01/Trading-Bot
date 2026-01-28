"""Frontend Views for the backtesting app."""

from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse_lazy

from .models import BacktestRun, BacktestTrade, BacktestResult


class BacktestListView(ListView):
    model = BacktestRun
    template_name = 'backtesting/backtest_list.html'
    context_object_name = 'backtests'
    paginate_by = 20


class BacktestDetailView(DetailView):
    model = BacktestRun
    template_name = 'backtesting/backtest_detail.html'
    context_object_name = 'backtest'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trades'] = BacktestTrade.objects.filter(backtest_run=self.object)[:50]
        try:
            context['results'] = BacktestResult.objects.get(backtest_run=self.object)
        except BacktestResult.DoesNotExist:
            context['results'] = None
        return context


class BacktestDashboardView(TemplateView):
    template_name = 'backtesting/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_backtests'] = BacktestRun.objects.order_by('-created_at')[:10]
        context['completed'] = BacktestRun.objects.filter(status='completed').count()
        context['running'] = BacktestRun.objects.filter(status='running').count()
        return context
