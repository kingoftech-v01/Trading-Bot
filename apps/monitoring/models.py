"""Models for the monitoring app."""

from django.db import models
from apps.core.models import BaseModel


class Alert(BaseModel):
    """System alerts and notifications."""

    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]

    TYPE_CHOICES = [
        ('signal', 'Signal Generated'),
        ('trade', 'Trade Executed'),
        ('risk', 'Risk Alert'),
        ('system', 'System Alert'),
        ('error', 'Error'),
    ]

    alert_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    title = models.CharField(max_length=200)
    message = models.TextField()
    source = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity.upper()}] {self.title}"


class HealthCheck(BaseModel):
    """System health check records."""

    COMPONENT_CHOICES = [
        ('database', 'Database'),
        ('redis', 'Redis'),
        ('celery', 'Celery'),
        ('exchange', 'Exchange API'),
        ('data_feed', 'Data Feed'),
    ]

    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('degraded', 'Degraded'),
        ('unhealthy', 'Unhealthy'),
    ]

    component = models.CharField(max_length=50, choices=COMPONENT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    response_time_ms = models.IntegerField(null=True, blank=True)
    details = models.JSONField(default=dict)
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Health Check'
        verbose_name_plural = 'Health Checks'
        ordering = ['-checked_at']

    def __str__(self):
        return f"{self.component}: {self.status}"


class SystemMetric(BaseModel):
    """System performance metrics."""

    name = models.CharField(max_length=100)
    value = models.FloatField()
    unit = models.CharField(max_length=50, blank=True)
    tags = models.JSONField(default=dict)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'System Metric'
        verbose_name_plural = 'System Metrics'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['name', 'recorded_at']),
        ]

    def __str__(self):
        return f"{self.name}: {self.value} {self.unit}"


class Report(BaseModel):
    """Generated reports."""

    TYPE_CHOICES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('custom', 'Custom Report'),
    ]

    report_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    data = models.JSONField(default=dict)
    summary = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.period_start.date()} - {self.period_end.date()})"
