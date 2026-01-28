"""
Frontend Views for the risk_management app.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages

from .models import RiskProfile, PositionSizeCalculation, DailyRiskTracker
from .forms import RiskProfileForm, CalculatePositionSizeForm
from .services import RiskManager, PositionSizer


class RiskProfileListView(ListView):
    """List risk profiles."""
    model = RiskProfile
    template_name = 'risk_management/profile_list.html'
    context_object_name = 'profiles'


class RiskProfileDetailView(DetailView):
    """View risk profile details."""
    model = RiskProfile
    template_name = 'risk_management/profile_detail.html'
    context_object_name = 'profile'


class RiskProfileCreateView(CreateView):
    """Create risk profile."""
    model = RiskProfile
    form_class = RiskProfileForm
    template_name = 'risk_management/profile_form.html'
    success_url = reverse_lazy('frontend:risk_management:profile_list')


class RiskProfileUpdateView(UpdateView):
    """Update risk profile."""
    model = RiskProfile
    form_class = RiskProfileForm
    template_name = 'risk_management/profile_form.html'

    def get_success_url(self):
        return reverse_lazy('frontend:risk_management:profile_detail', kwargs={'pk': self.object.pk})


class CalculatorView(TemplateView):
    """Position size calculator."""
    template_name = 'risk_management/calculator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CalculatePositionSizeForm()
        return context

    def post(self, request, *args, **kwargs):
        form = CalculatePositionSizeForm(request.POST)
        context = self.get_context_data()

        if form.is_valid():
            sizer = PositionSizer()
            data = form.cleaned_data

            if data.get('take_profit'):
                result = sizer.calculate_with_take_profit(
                    entry_price=data['entry_price'],
                    stop_loss=data['stop_loss'],
                    take_profit=data['take_profit'],
                    direction=data['direction'],
                )
            else:
                result = sizer.calculate_position_size(
                    entry_price=data['entry_price'],
                    stop_loss=data['stop_loss'],
                    direction=data['direction'],
                )

            context['result'] = result.data if result.success else None
            context['error'] = result.error if not result.success else None

        context['form'] = form
        return self.render_to_response(context)


class RiskDashboardView(TemplateView):
    """Risk management dashboard."""
    template_name = 'risk_management/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manager = RiskManager()
        result = manager.get_risk_summary()
        context['summary'] = result.data if result.success else None
        context['recent_calculations'] = PositionSizeCalculation.objects.order_by('-created_at')[:10]
        return context
