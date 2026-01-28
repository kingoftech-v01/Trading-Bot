"""Serializers for the monitoring app."""

from rest_framework import serializers
from .models import Alert, HealthCheck, SystemMetric, Report


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class HealthCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthCheck
        fields = '__all__'


class SystemMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemMetric
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
