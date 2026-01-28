"""Admin configuration for the monitoring app."""

from django.contrib import admin
from .models import Alert, HealthCheck, SystemMetric, Report


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'alert_type', 'severity', 'status', 'created_at']
    list_filter = ['alert_type', 'severity', 'status']
    search_fields = ['title', 'message']
    date_hierarchy = 'created_at'


@admin.register(HealthCheck)
class HealthCheckAdmin(admin.ModelAdmin):
    list_display = ['component', 'status', 'response_time_ms', 'checked_at']
    list_filter = ['component', 'status']
    date_hierarchy = 'checked_at'


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ['name', 'value', 'unit', 'recorded_at']
    list_filter = ['name']
    date_hierarchy = 'recorded_at'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'period_start', 'period_end', 'created_at']
    list_filter = ['report_type']
    date_hierarchy = 'created_at'
