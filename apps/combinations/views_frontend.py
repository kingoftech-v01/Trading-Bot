"""
Frontend Views for the combinations app.

Following URL_AND_VIEW_CONVENTIONS.md:
- Namespace: frontend:combinations
- HTML template responses
- Uses Django generic views
"""

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

from .models import Combination, CombinationResult
from .forms import (
    CombinationForm,
    CombinationFilterForm,
    EvaluateCombinationForm,
    CombinationResultFilterForm,
)
from .services import CombinationEvaluator
from apps.market_data.models import TradingPair, OHLCV


class CombinationListView(ListView):
    """
    List all combinations.

    GET /combinations/
    Template: combinations/combination_list.html
    """

    model = Combination
    template_name = 'combinations/combination_list.html'
    context_object_name = 'combinations'
    paginate_by = 20

    def get_queryset(self):
        queryset = Combination.objects.filter(is_active=True)
        form = CombinationFilterForm(self.request.GET)

        if form.is_valid():
            if form.cleaned_data.get('is_active') is not None:
                queryset = queryset.filter(
                    is_active=form.cleaned_data['is_active']
                )
            if form.cleaned_data.get('min_win_rate'):
                queryset = queryset.filter(
                    win_rate__gte=form.cleaned_data['min_win_rate']
                )
            if form.cleaned_data.get('min_risk_reward'):
                queryset = queryset.filter(
                    risk_reward_ratio__gte=form.cleaned_data['min_risk_reward']
                )

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = CombinationFilterForm(self.request.GET)
        return context


class CombinationDetailView(DetailView):
    """
    View combination details.

    GET /combinations/<uuid:pk>/
    Template: combinations/combination_detail.html
    """

    model = Combination
    template_name = 'combinations/combination_detail.html'
    context_object_name = 'combination'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get recent results for this combination
        context['recent_results'] = CombinationResult.objects.filter(
            combination=self.object
        ).order_by('-evaluated_at')[:10]
        return context


class CombinationCreateView(CreateView):
    """
    Create a new combination.

    GET/POST /combinations/create/
    Template: combinations/combination_form.html
    """

    model = Combination
    form_class = CombinationForm
    template_name = 'combinations/combination_form.html'
    success_url = reverse_lazy('frontend:combinations:combination_list')

    def form_valid(self, form):
        messages.success(self.request, 'Combination created successfully.')
        return super().form_valid(form)


class CombinationUpdateView(UpdateView):
    """
    Update an existing combination.

    GET/POST /combinations/<uuid:pk>/edit/
    Template: combinations/combination_form.html
    """

    model = Combination
    form_class = CombinationForm
    template_name = 'combinations/combination_form.html'

    def get_success_url(self):
        return reverse_lazy(
            'frontend:combinations:combination_detail',
            kwargs={'pk': self.object.pk}
        )

    def form_valid(self, form):
        messages.success(self.request, 'Combination updated successfully.')
        return super().form_valid(form)


class CombinationDeleteView(DeleteView):
    """
    Delete a combination.

    GET/POST /combinations/<uuid:pk>/delete/
    Template: combinations/combination_confirm_delete.html
    """

    model = Combination
    template_name = 'combinations/combination_confirm_delete.html'
    success_url = reverse_lazy('frontend:combinations:combination_list')

    def form_valid(self, form):
        messages.success(self.request, 'Combination deleted successfully.')
        return super().form_valid(form)


class CombinationResultListView(ListView):
    """
    List combination evaluation results.

    GET /combinations/results/
    Template: combinations/result_list.html
    """

    model = CombinationResult
    template_name = 'combinations/result_list.html'
    context_object_name = 'results'
    paginate_by = 50

    def get_queryset(self):
        queryset = CombinationResult.objects.select_related(
            'combination', 'trading_pair'
        ).order_by('-evaluated_at')

        form = CombinationResultFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('combination'):
                queryset = queryset.filter(
                    combination_id=form.cleaned_data['combination']
                )
            if form.cleaned_data.get('trading_pair'):
                queryset = queryset.filter(
                    trading_pair_id=form.cleaned_data['trading_pair']
                )
            if form.cleaned_data.get('signal'):
                queryset = queryset.filter(
                    signal=form.cleaned_data['signal']
                )
            if form.cleaned_data.get('timeframe'):
                queryset = queryset.filter(
                    timeframe=form.cleaned_data['timeframe']
                )
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(
                    evaluated_at__gte=form.cleaned_data['date_from']
                )
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(
                    evaluated_at__lte=form.cleaned_data['date_to']
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = CombinationResultFilterForm(self.request.GET)
        return context


class CombinationResultDetailView(DetailView):
    """
    View combination result details.

    GET /combinations/results/<uuid:pk>/
    Template: combinations/result_detail.html
    """

    model = CombinationResult
    template_name = 'combinations/result_detail.html'
    context_object_name = 'result'


class EvaluateCombinationsView(TemplateView):
    """
    Evaluate combinations for a trading pair.

    GET/POST /combinations/evaluate/
    Template: combinations/evaluate.html
    """

    template_name = 'combinations/evaluate.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trading_pairs = TradingPair.objects.filter(is_active=True)
        combinations = Combination.objects.filter(is_active=True)

        context['form'] = EvaluateCombinationForm(
            trading_pairs=trading_pairs,
            combinations=combinations
        )
        context['trading_pairs'] = trading_pairs
        context['combinations'] = combinations
        return context

    def post(self, request, *args, **kwargs):
        trading_pairs = TradingPair.objects.filter(is_active=True)
        combinations = Combination.objects.filter(is_active=True)

        form = EvaluateCombinationForm(
            request.POST,
            trading_pairs=trading_pairs,
            combinations=combinations
        )

        if form.is_valid():
            trading_pair_id = form.cleaned_data['trading_pair']
            timeframe = form.cleaned_data['timeframe']
            combination_name = form.cleaned_data.get('combination')

            try:
                trading_pair = TradingPair.objects.get(id=trading_pair_id)
            except TradingPair.DoesNotExist:
                messages.error(request, 'Trading pair not found.')
                return self.render_to_response(self.get_context_data())

            # Get OHLCV data
            ohlcv_qs = OHLCV.objects.filter(
                trading_pair=trading_pair,
                timeframe=timeframe
            ).order_by('-timestamp')[:200]

            if not ohlcv_qs.exists():
                messages.error(request, 'No OHLCV data available.')
                return self.render_to_response(self.get_context_data())

            ohlcv_data = list(ohlcv_qs.values(
                'timestamp', 'open', 'high', 'low', 'close', 'volume'
            ))
            ohlcv_data.reverse()

            evaluator = CombinationEvaluator()

            if combination_name:
                # Evaluate single combination
                results = evaluator.evaluate_single(combination_name, ohlcv_data)
            else:
                # Evaluate all combinations
                results = evaluator.evaluate_all(ohlcv_data)

            context = self.get_context_data()
            context['results'] = results
            context['trading_pair'] = trading_pair
            context['timeframe'] = timeframe
            return self.render_to_response(context)

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class CombinationInfoView(TemplateView):
    """
    View information about all combinations.

    GET /combinations/info/
    Template: combinations/info.html
    """

    template_name = 'combinations/info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evaluator = CombinationEvaluator()
        context['combination_info'] = evaluator.get_combination_info()
        return context
