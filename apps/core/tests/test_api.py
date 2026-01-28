"""
Tests for Core API Views.

Tests the health check endpoint and base viewset functionality.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


class HealthCheckAPITestCase(APITestCase):
    """Test cases for health check API endpoint."""

    def test_health_check_returns_200(self):
        """Test that health check returns 200 OK."""
        url = '/api/v1/core/health/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_returns_healthy_status(self):
        """Test that health check returns healthy status."""
        url = '/api/v1/core/health/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')

    def test_health_check_returns_version(self):
        """Test that health check returns version info."""
        url = '/api/v1/core/health/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('version', response.data)
        self.assertEqual(response.data['version'], '1.0.0')

    def test_health_check_json_content_type(self):
        """Test that health check returns JSON content type."""
        url = '/api/v1/core/health/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_health_check_only_allows_get(self):
        """Test that health check only allows GET method."""
        url = '/api/v1/core/health/'

        # POST should fail
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # PUT should fail
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # DELETE should fail
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class BaseModelViewSetTestCase(APITestCase):
    """Test cases for BaseModelViewSet functionality."""

    def test_base_viewset_has_perform_destroy(self):
        """Test that BaseModelViewSet has perform_destroy method."""
        from apps.core.views_api import BaseModelViewSet
        self.assertTrue(hasattr(BaseModelViewSet, 'perform_destroy'))

    def test_base_viewset_has_get_queryset(self):
        """Test that BaseModelViewSet has get_queryset method."""
        from apps.core.views_api import BaseModelViewSet
        self.assertTrue(hasattr(BaseModelViewSet, 'get_queryset'))
