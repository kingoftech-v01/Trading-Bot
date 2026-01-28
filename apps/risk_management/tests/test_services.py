"""
Tests for risk_management services.
"""

from django.test import TestCase
from decimal import Decimal

from apps.risk_management.models import RiskProfile
from apps.risk_management.services import (
    PositionSizer, StopLossCalculator, TakeProfitCalculator, RiskManager
)


class PositionSizerTest(TestCase):
    def setUp(self):
        self.profile = RiskProfile.objects.create(
            name='Test Profile',
            account_balance=Decimal('10000'),
            risk_per_trade=Decimal('0.01'),
            min_risk_reward=Decimal('3.0'),
            is_default=True,
        )
        self.sizer = PositionSizer(self.profile)

    def test_calculate_position_size_buy(self):
        result = self.sizer.calculate_position_size(
            entry_price=Decimal('100'),
            stop_loss=Decimal('95'),
            direction='buy',
        )
        self.assertTrue(result.success)
        self.assertIn('position_size', result.data)
        self.assertEqual(result.data['risk_amount'], 100.0)  # 1% of 10000

    def test_calculate_position_size_sell(self):
        result = self.sizer.calculate_position_size(
            entry_price=Decimal('100'),
            stop_loss=Decimal('105'),
            direction='sell',
        )
        self.assertTrue(result.success)

    def test_calculate_with_take_profit(self):
        result = self.sizer.calculate_with_take_profit(
            entry_price=Decimal('100'),
            stop_loss=Decimal('95'),
            take_profit=Decimal('115'),
            direction='buy',
        )
        self.assertTrue(result.success)
        self.assertIn('risk_reward_ratio', result.data)


class StopLossCalculatorTest(TestCase):
    def setUp(self):
        self.calculator = StopLossCalculator()

    def test_atr_based(self):
        result = self.calculator.calculate_atr_based(
            entry_price=Decimal('100'),
            atr=Decimal('2'),
            direction='buy',
            multiplier=2.0,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data['stop_loss'], 96.0)

    def test_percentage_based(self):
        result = self.calculator.calculate_percentage_based(
            entry_price=Decimal('100'),
            direction='buy',
            percentage=0.02,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data['stop_loss'], 98.0)


class TakeProfitCalculatorTest(TestCase):
    def setUp(self):
        self.calculator = TakeProfitCalculator()

    def test_risk_reward_based(self):
        result = self.calculator.calculate_risk_reward_based(
            entry_price=Decimal('100'),
            stop_loss=Decimal('95'),
            direction='buy',
            risk_reward=3.0,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data['take_profit'], 115.0)
