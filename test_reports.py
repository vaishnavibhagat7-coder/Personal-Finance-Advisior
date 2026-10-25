from datetime import date
from decimal import Decimal
from app.models import Income, Expense, ExpenseCategory
from app.extensions import db


def test_monthly_report_view_and_calculations(auth_client_a, app, user_a):
    """Test monthly statement figures rendering."""
    today = date.today()
    with app.app_context():
        db.session.add(Income(user_id=user_a.id, source='Salary', amount=Decimal('55000.00'), date=today))
        cat = ExpenseCategory.query.filter_by(name='Rent and Housing').first()
        db.session.add(Expense(user_id=user_a.id, category_id=cat.id, amount=Decimal('20000.00'), date=today))
        db.session.commit()

    res = auth_client_a.get(f'/reports/?month={today.month}&year={today.year}')
    assert res.status_code == 200
    assert b'Monthly Financial Statement' in res.data
    assert b'Rent and Housing' in res.data


def test_transactions_csv_export(auth_client_a, app, user_a):
    """Test downloading the transactions CSV export."""
    today = date.today()
    with app.app_context():
        db.session.add(Income(user_id=user_a.id, source='Freelance', amount=Decimal('12000.00'), date=today, description='Consulting gig'))
        cat = ExpenseCategory.query.filter_by(name='Groceries').first()
        db.session.add(Expense(user_id=user_a.id, category_id=cat.id, amount=Decimal('3500.00'), date=today, merchant='Supermarket'))
        db.session.commit()

    res = auth_client_a.get(f'/reports/export/transactions.csv?month={today.month}&year={today.year}')
    assert res.status_code == 200
    assert res.headers['Content-Type'].startswith('text/csv')
    assert 'attachment; filename=' in res.headers['Content-Disposition']

    csv_text = res.data.decode('utf-8')
    assert 'Type,Date,Category/Source,Payment Method,Merchant/Description,Amount,Currency' in csv_text
    assert 'Income' in csv_text
    assert 'Freelance' in csv_text
    assert '12000.00' in csv_text
    assert 'Expense' in csv_text
    assert 'Groceries' in csv_text
    assert '3500.00' in csv_text


def test_summary_csv_export(auth_client_a, app, user_a):
    """Test downloading the summary CSV export."""
    today = date.today()
    with app.app_context():
        db.session.add(Income(user_id=user_a.id, source='Salary', amount=Decimal('30000.00'), date=today))
        db.session.commit()

    res = auth_client_a.get(f'/reports/export/summary.csv?month={today.month}&year={today.year}')
    assert res.status_code == 200
    assert res.headers['Content-Type'].startswith('text/csv')

    csv_text = res.data.decode('utf-8')
    assert 'FinWise AI - Financial Summary Report' in csv_text
    assert 'Total Income' in csv_text
    assert '30000.00' in csv_text
