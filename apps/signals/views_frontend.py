"""
Frontend Views for the signals app.

Following URL_AND_VIEW_CONVENTIONS.md:
- Namespace: frontend:signals
- HTML template responses
- Uses Django generic views
"""

from django.views.generic import (
    ListView,
    DetailView,
    TemplateView,
)
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .models import Vote, SignalSession, Signal, ConfluenceScore
from .forms import (
    GenerateSignalForm,
    SignalFilterForm,
    SignalSessionFilterForm,
    SignalActionForm,
)
from .services import SignalGenerator, VotingSystem
from apps.market_data.models import TradingPair, OHLCV


class SignalListView(ListView):
    """
    List all signals.

    GET /signals/
    Template: signals/signal_list.html
    """

    model = Signal
    template_name = 'signals/signal_list.html'
    context_object_name = 'signals'
    paginate_by = 50

    def get_queryset(self):
        queryset = Signal.objects.select_related(
            'trading_pair', 'session'
        ).order_by('-created_at')

        form = SignalFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('trading_pair'):
                queryset = queryset.filter(
                    trading_pair_id=form.cleaned_data['trading_pair']
                )
            if form.cleaned_data.get('signal'):
                queryset = queryset.filter(
                    signal=form.cleaned_data['signal']
                )
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(
                    status=form.cleaned_data['status']
                )
            if form.cleaned_data.get('timeframe'):
                queryset = queryset.filter(
                    timeframe=form.cleaned_data['timeframe']
                )
            if form.cleaned_data.get('min_confluence'):
                queryset = queryset.filter(
                    confluence_score__gte=form.cleaned_data['min_confluence']
                )
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(
                    created_at__gte=form.cleaned_data['date_from']
                )
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(
                    created_at__lte=form.cleaned_data['date_to']
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = SignalFilterForm(self.request.GET)

        # Add summary stats
        context['active_signals'] = Signal.objects.filter(
            status='pending',
            expires_at__gt=timezone.now(),
        ).count()
        context['total_signals'] = Signal.objects.count()

        return context


class SignalDetailView(DetailView):
    """
    View signal details.

    GET /signals/<uuid:pk>/
    Template: signals/signal_detail.html
    """

    model = Signal
    template_name = 'signals/signal_detail.html'
    context_object_name = 'signal'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_form'] = SignalActionForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = SignalActionForm(request.POST)

        if form.is_valid():
            action = form.cleaned_data['action']
            if action == 'execute':
                self.object.mark_executed()
                messages.success(request, 'Signal marked as executed.')
            elif action == 'cancel':
                self.object.mark_cancelled()
                messages.success(request, 'Signal cancelled.')

        return redirect('frontend:signals:signal_detail', pk=self.object.pk)


class ActiveSignalsView(ListView):
    """
    List active signals only.

    GET /signals/active/
    Template: signals/active_signals.html
    """

    model = Signal
    template_name = 'signals/active_signals.html'
    context_object_name = 'signals'

    def get_queryset(self):
        return Signal.objects.filter(
            status='pending',
            expires_at__gt=timezone.now(),
        ).select_related(
            'trading_pair', 'session'
        ).order_by('-created_at')


class SignalSessionListView(ListView):
    """
    List signal sessions.

    GET /signals/sessions/
    Template: signals/session_list.html
    """

    model = SignalSession
    template_name = 'signals/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 50

    def get_queryset(self):
        queryset = SignalSession.objects.select_related(
            'trading_pair'
        ).order_by('-evaluated_at')

        form = SignalSessionFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('trading_pair'):
                queryset = queryset.filter(
                    trading_pair_id=form.cleaned_data['trading_pair']
                )
            if form.cleaned_data.get('final_signal'):
                queryset = queryset.filter(
                    final_signal=form.cleaned_data['final_signal']
                )
            if form.cleaned_data.get('timeframe'):
                queryset = queryset.filter(
                    timeframe=form.cleaned_data['timeframe']
                )
            if form.cleaned_data.get('actionable_only'):
                queryset = queryset.filter(
                    final_signal__in=['buy', 'sell']
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = SignalSessionFilterForm(self.request.GET)
        return context


class SignalSessionDetailView(DetailView):
    """
    View session details with all votes.

    GET /signals/sessions/<uuid:pk>/
    Template: signals/session_detail.html
    """

    model = SignalSession
    template_name = 'signals/session_detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['votes'] = Vote.objects.filter(
            signal_session=self.object
        ).select_related('combination')

        # Get confluence score if exists
        try:
            context['confluence_detail'] = ConfluenceScore.objects.get(
                session=self.object
            )
        except ConfluenceScore.DoesNotExist:
            context['confluence_detail'] = None

        return context


class GenerateSignalView(TemplateView):
    """
    Generate signals for a trading pair.

    GET/POST /signals/generate/
    Template: signals/generate.html
    """

    template_name = 'signals/generate.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trading_pairs = TradingPair.objects.filter(is_active=True)
        context['form'] = GenerateSignalForm(trading_pairs=trading_pairs)
        context['trading_pairs'] = trading_pairs
        return context

    def post(self, request, *args, **kwargs):
        trading_pairs = TradingPair.objects.filter(is_active=True)
        form = GenerateSignalForm(request.POST, trading_pairs=trading_pairs)

        if form.is_valid():
            trading_pair_id = form.cleaned_data['trading_pair']
            timeframe = form.cleaned_data['timeframe']
            min_confluence = form.cleaned_data['min_confluence']
            min_confidence = form.cleaned_data['min_confidence']

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

            # Generate signal
            generator = SignalGenerator(
                min_confluence=min_confluence,
                min_confidence=min_confidence,
            )
            result = generator.generate_signal(
                trading_pair=trading_pair,
                ohlcv_data=ohlcv_data,
                timeframe=timeframe,
            )

            context = self.get_context_data()
            context['result'] = result.data if result.success else None
            context['error'] = result.error if not result.success else None
            context['trading_pair'] = trading_pair
            context['timeframe'] = timeframe

            if result.success and result.data.get('signal_generated'):
                messages.success(
                    request,
                    f"Signal generated: {result.data['signal'].upper()}"
                )
            elif result.success:
                messages.info(request, f"No signal: {result.data.get('reason')}")

            return self.render_to_response(context)

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class VotingStatusView(TemplateView):
    """
    View current voting status for pairs.

    GET /signals/voting-status/
    Template: signals/voting_status.html
    """

    template_name = 'signals/voting_status.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trading_pairs'] = TradingPair.objects.filter(is_active=True)
        return context


class SignalDashboardView(TemplateView):
    """
    Signal generation dashboard overview.

    GET /signals/dashboard/
    Template: signals/dashboard.html
    """

    template_name = 'signals/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Recent signals
        context['recent_signals'] = Signal.objects.select_related(
            'trading_pair'
        ).order_by('-created_at')[:10]

        # Active signals
        context['active_signals'] = Signal.objects.filter(
            status='pending',
            expires_at__gt=timezone.now(),
        ).select_related('trading_pair')

        # Recent sessions
        context['recent_sessions'] = SignalSession.objects.select_related(
            'trading_pair'
        ).order_by('-evaluated_at')[:10]

        # Statistics
        context['stats'] = {
            'total_signals': Signal.objects.count(),
            'active_count': context['active_signals'].count(),
            'buy_signals': Signal.objects.filter(signal='buy').count(),
            'sell_signals': Signal.objects.filter(signal='sell').count(),
            'executed_signals': Signal.objects.filter(status='executed').count(),
        }

        return context
