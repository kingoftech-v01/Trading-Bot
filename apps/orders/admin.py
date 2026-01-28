"""Admin configuration for the orders app."""

from django.contrib import admin
from .models import Order, Trade, Position


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['trading_pair', 'side', 'order_type', 'quantity', 'price', 'status', 'created_at']
    list_filter = ['status', 'side', 'order_type']
    search_fields = ['trading_pair__symbol']
    date_hierarchy = 'created_at'


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['trading_pair', 'side', 'entry_price', 'exit_price', 'realized_pnl', 'status', 'opened_at']
    list_filter = ['status', 'side', 'close_reason']
    search_fields = ['trading_pair__symbol']
    date_hierarchy = 'opened_at'


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['trading_pair', 'side', 'quantity', 'average_entry_price', 'unrealized_pnl', 'is_active']
    list_filter = ['side', 'is_active']
    search_fields = ['trading_pair__symbol']
