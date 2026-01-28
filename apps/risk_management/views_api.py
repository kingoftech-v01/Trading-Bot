"""
API Views for the risk_management app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RiskProfile, PositionSizeCalculation, DailyRiskTracker
from .serializers import (
    RiskProfileSerializer,
    PositionSizeCalculationSerializer,
    DailyRiskTrackerSerializer,
    CalculatePositionSizeSerializer,
)
from .services import RiskManager, PositionSizer


class RiskProfileViewSet(viewsets.ModelViewSet):
    """API endpoint for RiskProfile CRUD."""

    queryset = RiskProfile.objects.filter(is_active=True)
    serializer_class = RiskProfileSerializer

    @action(detail=False, methods=['get'])
    def default(self, request):
        """Get default risk profile."""
        try:
            profile = RiskProfile.objects.get(is_default=True)
            serializer = RiskProfileSerializer(profile)
            return Response(serializer.data)
        except RiskProfile.DoesNotExist:
            return Response(
                {'error': 'No default profile'},
                status=status.HTTP_404_NOT_FOUND
            )


class PositionSizeCalculationViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for PositionSizeCalculation."""

    queryset = PositionSizeCalculation.objects.select_related(
        'risk_profile', 'trading_pair'
    ).order_by('-created_at')
    serializer_class = PositionSizeCalculationSerializer


class DailyRiskTrackerViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for DailyRiskTracker."""

    queryset = DailyRiskTracker.objects.select_related(
        'risk_profile'
    ).order_by('-date')
    serializer_class = DailyRiskTrackerSerializer


class CalculatePositionSizeAPIView(APIView):
    """Calculate position size."""

    def post(self, request):
        serializer = CalculatePositionSizeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        sizer = PositionSizer()

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

        if result.success:
            return Response(result.data)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)


class RiskSummaryAPIView(APIView):
    """Get risk summary."""

    def get(self, request):
        manager = RiskManager()
        result = manager.get_risk_summary()

        if result.success:
            return Response(result.data)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)
