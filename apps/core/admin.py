"""
Core Admin - Base admin configuration.

This module provides base admin classes for the trading bot.
"""

from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    """
    Base admin class for all models.

    Provides common functionality and display settings.
    """
    list_display = ['id', 'created_at', 'updated_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self, request):
        """Show all records including inactive ones in admin."""
        return super().get_queryset(request)

    actions = ['soft_delete_selected', 'restore_selected']

    @admin.action(description='Soft delete selected items')
    def soft_delete_selected(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description='Restore selected items')
    def restore_selected(self, request, queryset):
        queryset.update(is_active=True)
