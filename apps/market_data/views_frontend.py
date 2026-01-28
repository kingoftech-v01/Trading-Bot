"""
Market Data Frontend Views - HTML template views.

Provides template-based views for:
- Exchange list and detail
- TradingPair list and detail
- OHLCV data visualization
- Data management dashboard

URL namespace: frontend:market_data
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max
from django.utils.translation import gettext_lazy as _

from .models import Exchange, TradingPair, OHLCV, CorrelationMatrix
from .forms import ExchangeForm, TradingPairForm, FetchDataForm


@login_required
def exchange_list(request):
    """
    List all exchanges with filtering and pagination.

    Template: market_data/exchange_list.html
    """
    search = request.GET.get('search', '').strip()
    api_type = request.GET.get('api_type')
    page = request.GET.get('page', 1)

    exchanges = Exchange.objects.filter(is_active=True)

    if search:
        exchanges = exchanges.filter(name__icontains=search)

    if api_type:
        exchanges = exchanges.filter(api_type=api_type)

    exchanges = exchanges.annotate(
        pairs_count=Count('trading_pairs')
    ).order_by('name')

    paginator = Paginator(exchanges, 20)
    exchanges_page = paginator.get_page(page)

    context = {
        'exchanges': exchanges_page,
        'search': search,
        'api_type': api_type,
        'page_title': _('Exchanges'),
    }

    return render(request, 'market_data/exchange_list.html', context)


@login_required
def exchange_detail(request, pk):
    """
    Display exchange details with related trading pairs.

    Template: market_data/exchange_detail.html
    """
    exchange = get_object_or_404(Exchange, pk=pk, is_active=True)
    trading_pairs = exchange.trading_pairs.filter(is_active=True)

    context = {
        'exchange': exchange,
        'trading_pairs': trading_pairs,
        'page_title': exchange.name,
    }

    return render(request, 'market_data/exchange_detail.html', context)


@login_required
def trading_pair_list(request):
    """
    List all trading pairs with filtering and pagination.

    Template: market_data/trading_pair_list.html
    """
    search = request.GET.get('search', '').strip()
    exchange_id = request.GET.get('exchange')
    is_forex = request.GET.get('is_forex')
    page = request.GET.get('page', 1)

    pairs = TradingPair.objects.filter(is_active=True).select_related('exchange')

    if search:
        pairs = pairs.filter(
            Q(symbol__icontains=search) |
            Q(base_currency__icontains=search) |
            Q(quote_currency__icontains=search)
        )

    if exchange_id:
        pairs = pairs.filter(exchange_id=exchange_id)

    if is_forex:
        pairs = pairs.filter(is_forex=(is_forex.lower() == 'true'))

    # Annotate with latest data timestamp
    pairs = pairs.annotate(
        latest_data=Max('ohlcv_data__timestamp')
    ).order_by('symbol')

    paginator = Paginator(pairs, 20)
    pairs_page = paginator.get_page(page)

    context = {
        'trading_pairs': pairs_page,
        'exchanges': Exchange.objects.filter(is_active=True),
        'search': search,
        'exchange_id': exchange_id,
        'is_forex': is_forex,
        'page_title': _('Trading Pairs'),
    }

    return render(request, 'market_data/trading_pair_list.html', context)


@login_required
def trading_pair_detail(request, pk):
    """
    Display trading pair details with recent OHLCV data.

    Template: market_data/trading_pair_detail.html
    """
    pair = get_object_or_404(
        TradingPair.objects.select_related('exchange'),
        pk=pk,
        is_active=True
    )

    # Get recent OHLCV data for each timeframe
    recent_data = {}
    for timeframe, _ in OHLCV.TIMEFRAME_CHOICES:
        recent_data[timeframe] = pair.ohlcv_data.filter(
            timeframe=timeframe
        ).order_by('-timestamp')[:10]

    # Get correlations
    correlations = CorrelationMatrix.objects.filter(
        Q(primary_pair=pair) | Q(secondary_pair=pair)
    ).select_related('primary_pair', 'secondary_pair')[:10]

    context = {
        'trading_pair': pair,
        'recent_data': recent_data,
        'correlations': correlations,
        'page_title': pair.display_symbol,
    }

    return render(request, 'market_data/trading_pair_detail.html', context)


@login_required
def trading_pair_create(request):
    """
    Create a new trading pair.

    Template: market_data/trading_pair_form.html
    """
    if request.method == 'POST':
        form = TradingPairForm(request.POST)
        if form.is_valid():
            pair = form.save()
            messages.success(request, _('Trading pair created successfully'))
            return redirect('market_data-frontend:trading_pair_detail', pk=pair.pk)
    else:
        form = TradingPairForm()

    context = {
        'form': form,
        'form_title': _('Create Trading Pair'),
        'submit_text': _('Create'),
        'page_title': _('Create Trading Pair'),
    }

    return render(request, 'market_data/trading_pair_form.html', context)


@login_required
def ohlcv_chart(request, trading_pair_id):
    """
    Display OHLCV chart for a trading pair.

    Template: market_data/ohlcv_chart.html
    """
    pair = get_object_or_404(TradingPair, pk=trading_pair_id, is_active=True)
    timeframe = request.GET.get('timeframe', '1h')

    context = {
        'trading_pair': pair,
        'timeframe': timeframe,
        'page_title': f"{pair.display_symbol} Chart",
    }

    return render(request, 'market_data/ohlcv_chart.html', context)


@login_required
def data_dashboard(request):
    """
    Market data management dashboard.

    Template: market_data/dashboard.html
    """
    # Statistics
    stats = {
        'exchange_count': Exchange.objects.filter(is_active=True).count(),
        'pair_count': TradingPair.objects.filter(is_active=True).count(),
        'forex_count': TradingPair.objects.filter(is_active=True, is_forex=True).count(),
        'crypto_count': TradingPair.objects.filter(is_active=True, is_forex=False).count(),
        'ohlcv_count': OHLCV.objects.count(),
    }

    # Recent data
    recent_pairs = TradingPair.objects.filter(is_active=True).annotate(
        latest_data=Max('ohlcv_data__timestamp'),
        data_count=Count('ohlcv_data')
    ).order_by('-latest_data')[:10]

    context = {
        'stats': stats,
        'recent_pairs': recent_pairs,
        'page_title': _('Market Data Dashboard'),
    }

    return render(request, 'market_data/dashboard.html', context)
