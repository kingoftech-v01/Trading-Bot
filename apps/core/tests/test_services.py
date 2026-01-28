"""
Tests for Core Services.

Tests the BaseService and ServiceResult classes.
"""

from django.test import TestCase
from apps.core.services.base_service import BaseService, ServiceResult


class ServiceResultTestCase(TestCase):
    """Test cases for ServiceResult."""

    def test_ok_result(self):
        """Test creating a successful result."""
        result = ServiceResult.ok(data={'key': 'value'})
        self.assertTrue(result.success)
        self.assertEqual(result.data, {'key': 'value'})
        self.assertIsNone(result.error)

    def test_fail_result(self):
        """Test creating a failed result."""
        result = ServiceResult.fail(error='Something went wrong')
        self.assertFalse(result.success)
        self.assertIsNone(result.data)
        self.assertEqual(result.error, 'Something went wrong')

    def test_bool_success(self):
        """Test boolean context for successful result."""
        result = ServiceResult.ok()
        self.assertTrue(bool(result))

    def test_bool_failure(self):
        """Test boolean context for failed result."""
        result = ServiceResult.fail('Error')
        self.assertFalse(bool(result))

    def test_fail_with_errors_dict(self):
        """Test failed result with errors dictionary."""
        errors = {'field1': 'Error 1', 'field2': 'Error 2'}
        result = ServiceResult.fail('Validation failed', errors=errors)
        self.assertFalse(result.success)
        self.assertEqual(result.errors, errors)
