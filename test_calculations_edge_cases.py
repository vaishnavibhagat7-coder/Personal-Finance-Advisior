from datetime import date
from decimal import Decimal
from app.advisor.service import aggregate_user_financial_data
from app.models import Income, Expense, ExpenseCategory
from app.utils import (
    to_decimal,
    format_indian_number,
    format_currency,
    format_percentage,
    get_month_bounds,
    shift_months
)
from app.extensions import db


def test_zero_income_calculation(app, user_a):
    """Test calculations when income is zero and expenses exist (no division by zero)."""
    today = date(2026, 5, 10)
    with app.app_context():
        cat = ExpenseCategory.query.filter_by(name='Rent and Housing').first()
        db.session.add(Expense(
            user_id=user_a.id,
            category_id=cat.id,
            amount=Decimal('12000.00'),
            date=today
        ))
        db.session.commit()

        data = aggregate_user_financial_data(user_a, 2026, 5)
        assert data['total_income'] == Decimal('0.00')
        assert data['total_expenses'] == Decimal('12000.00')
        assert data['net_balance'] == Decimal('-12000.00')
        assert data['savings_rate'] == Decimal('0.00')
        assert data['health_score'] < 60


def test_empty_transaction_history(app, user_a):
    """Test calculations with completely empty history."""
    with app.app_context():
        data = aggregate_user_financial_data(user_a, 2026, 1)
        assert data['total_income'] == Decimal('0.00')
        assert data['total_expenses'] == Decimal('0.00')
        assert data['net_balance'] == Decimal('0.00')
        assert data['savings_rate'] == Decimal('0.00')
        assert data['category_breakdown'] == []
        assert data['health_score'] >= 50


def test_large_financial_values(app, user_a):
    """Test calculations with large values (e.g. Crores) using exact Decimal precision."""
    d = date(2026, 7, 1)
    with app.app_context():
        # Income: 1 Crore (10,000,000)
        db.session.add(Income(
            user_id=user_a.id,
            source='Business',
            amount=Decimal('10000000.00'),
            date=d
        ))
        # Expense: 25 Lakhs (2,500,000)
        cat = ExpenseCategory.query.filter_by(name='Rent and Housing').first()
        db.session.add(Expense(
            user_id=user_a.id,
            category_id=cat.id,
            amount=Decimal('2500000.00'),
            date=d
        ))
        db.session.commit()

        data = aggregate_user_financial_data(user_a, 2026, 7)
        assert data['total_income'] == Decimal('10000000.00')
        assert data['total_expenses'] == Decimal('2500000.00')
        assert data['net_balance'] == Decimal('7500000.00')
        assert data['savings_rate'] == Decimal('75.0')


def test_indian_number_formatting():
    """Verify Indian numbering format representation."""
    assert format_indian_number(Decimal('1000.00')) == '1,000.00'
    assert format_indian_number(Decimal('25000.00')) == '25,000.00'
    assert format_indian_number(Decimal('150000.00')) == '1,50,000.00'
    assert format_indian_number(Decimal('10000000.00')) == '1,00,00,000.00'
    assert format_indian_number(Decimal('-5000.50')) == '-5,000.50'
    assert format_indian_number(None) == '0.00'


def test_currency_formatting():
    """Verify currency symbol placement with positive and negative numbers."""
    assert format_currency(Decimal('25000.00'), '₹') == '₹25,000.00'
    assert format_currency(Decimal('-15000.00'), '₹') == '-₹15,000.00'
    assert format_currency(Decimal('0.00'), '₹') == '₹0.00'


def test_month_bounds_and_leap_years():
    """Verify month boundary date calculation for standard and leap years."""
    # Leap year February (2024)
    start_24, end_24 = get_month_bounds(2024, 2)
    assert start_24 == date(2024, 2, 1)
    assert end_24 == date(2024, 2, 29)

    # Non-leap year February (2025)
    start_25, end_25 = get_month_bounds(2025, 2)
    assert start_25 == date(2025, 2, 1)
    assert end_25 == date(2025, 2, 28)

    # 31-day month (December)
    start_dec, end_dec = get_month_bounds(2026, 12)
    assert start_dec == date(2026, 12, 1)
    assert end_dec == date(2026, 12, 31)


def test_shift_months_helper():
    """Verify adding/subtracting months with end-of-month day clamping."""
    # Subtracting 6 months
    assert shift_months(date(2026, 10, 15), -6) == date(2026, 4, 15)

    # Clamping from Jan 31 to Feb 28 in non-leap year
    assert shift_months(date(2025, 1, 31), 1) == date(2025, 2, 28)

    # Clamping from Jan 31 to Feb 29 in leap year
    assert shift_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
