"""API Views for the monitoring app."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Alert, HealthCheck, Report
from .serializers import AlertSerializer, HealthCheckSerializer, ReportSerializer
from .services import AlertManager, HealthChecker, ReportGenerator


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.order_by('-created_at')
    serializer_class = AlertSerializer

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        manager = AlertManager()
        result = manager.acknowledge_alert(pk)
        if result.success:
            return Response(result.data)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        manager = AlertManager()
        result = manager.resolve_alert(pk)
        if result.success:
            return Response(result.data)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        manager = AlertManager()
        return Response(manager.get_alert_summary())


class HealthCheckViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HealthCheck.objects.order_by('-checked_at')
    serializer_class = HealthCheckSerializer


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Report.objects.order_by('-created_at')
    serializer_class = ReportSerializer


class HealthAPIView(APIView):
    def get(self, request):
        checker = HealthChecker()
        result = checker.check_all()
        if result.success:
            return Response(result.data)
        return Response({'error': result.error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerateReportAPIView(APIView):
    def post(self, request):
        report_type = request.data.get('type', 'daily')
        generator = ReportGenerator()

        if report_type == 'daily':
            result = generator.generate_daily_report()
        elif report_type == 'performance':
            days = int(request.data.get('days', 30))
            result = generator.generate_performance_summary(days)
        else:
            return Response({'error': 'Unknown report type'}, status=status.HTTP_400_BAD_REQUEST)

        if result.success:
            return Response(result.data)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)
