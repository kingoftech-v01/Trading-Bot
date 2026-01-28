"""
Core API Views - Base API views and utilities.

This module provides base viewset classes and API utilities.
Following URL_AND_VIEW_CONVENTIONS.md for API layer.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base viewset for all model viewsets.

    Provides common functionality like soft delete.
    """

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.soft_delete()

    def get_queryset(self):
        """Filter to only active records by default."""
        queryset = super().get_queryset()
        # Allow showing inactive records with ?show_inactive=true
        show_inactive = self.request.query_params.get('show_inactive', 'false')
        if show_inactive.lower() != 'true':
            queryset = queryset.filter(is_active=True)
        return queryset


@api_view(['GET'])
def health_check(request):
    """
    API health check endpoint.

    GET /api/v1/health/

    Returns:
        200: {"status": "healthy"}
    """
    return Response({
        'status': 'healthy',
        'version': '1.0.0',
    }, status=status.HTTP_200_OK)
