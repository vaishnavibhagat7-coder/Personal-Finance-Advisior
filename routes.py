import csv
import io
from datetime import date
from decimal import Decimal
from flask import Blueprint, render_template, request, Response, make_response
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Income, Expense, Budget, SavingsGoal
from app.utils import to_decimal, get_month_bounds, get_month_name, format_indian_number, shift_months
from app.advisor.service import aggregate_user_financial_data, query_gemini_advisor

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def index():
    today = date.today()
    selected_year = request.args.get('year', default=today.year, type=int)
    selected_month = request.args.get('month', default=today.month, type=int)

    start_date, end_date = get_month_bounds(selected_year, selected_month)

    # 1. Current Month Aggregates
    data = aggregate_user_financial_data(current_user, selected_year, selected_month)

    # 2. Previous Month Comparison
    prev_dt = shift_months(date(selected_year, selected_month, 1), -1)
    prev_data = aggregate_user_financial_data(current_user, prev_dt.year, prev_dt.month)

    income_change = data['total_income'] - prev_data['total_income']
    income_change_pct = (income_change / prev_data['total_income'] * Decimal('100.0')) if prev_data['total_income'] > 0 else None

    expense_change = data['total_expenses'] - prev_data['total_expenses']
    expense_change_pct = (expense_change / prev_data['total_expenses'] * Decimal('100.0')) if prev_data['total_expenses'] > 0 else None

    top_category = data['category_breakdown'][0] if data['category_breakdown'] else None

    # Get cached or live AI insight
    ai_insight, is_live_ai = query_gemini_advisor(data)

    month_names = [(m, get_month_name(m)) for m in range(1, 13)]
    years = [selected_year - 1, selected_year, selected_year + 1]

    return render_template(
        'reports/reports.html',
        data=data,
        prev_data=prev_data,
        income_change=income_change,
        income_change_pct=income_change_pct,
        expense_change=expense_change,
        expense_change_pct=expense_change_pct,
        top_category=top_category,
        ai_insight=ai_insight,
        is_live_ai=is_live_ai,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_month_name=get_month_name(selected_month),
        month_names=month_names,
        years=years
    )


@reports_bp.route('/export/transactions.csv')
@login_required
def export_transactions_csv():
    today = date.today()
    selected_year = request.args.get('year', default=today.year, type=int)
    selected_month = request.args.get('month', default=today.month, type=int)

    start_date, end_date = get_month_bounds(selected_year, selected_month)

    # Incomes
    incomes = Income.query.filter(
        Income.user_id == current_user.id,
        Income.date >= start_date,
        Income.date <= end_date
    ).order_by(Income.date.asc()).all()

    # Expenses
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).order_by(Expense.date.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow(['Type', 'Date', 'Category/Source', 'Payment Method', 'Merchant/Description', 'Amount', 'Currency'])

    for inc in incomes:
        writer.writerow([
            'Income',
            inc.date.strftime('%Y-%m-%d'),
            inc.source,
            'N/A',
            inc.description or '',
            f"{to_decimal(inc.amount):.2f}",
            current_user.currency
        ])

    for exp in expenses:
        writer.writerow([
            'Expense',
            exp.date.strftime('%Y-%m-%d'),
            exp.category.name if exp.category else 'Other',
            exp.payment_method,
            exp.merchant or exp.notes or '',
            f"{to_decimal(exp.amount):.2f}",
            current_user.currency
        ])

    csv_data = output.getvalue()
    filename = f"finwise_transactions_{selected_year}_{selected_month:02d}.csv"

    response = make_response(csv_data)
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response


@reports_bp.route('/export/summary.csv')
@login_required
def export_summary_csv():
    today = date.today()
    selected_year = request.args.get('year', default=today.year, type=int)
    selected_month = request.args.get('month', default=today.month, type=int)

    data = aggregate_user_financial_data(current_user, selected_year, selected_month)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['FinWise AI - Financial Summary Report'])
    writer.writerow(['User', current_user.full_name])
    writer.writerow(['Period', f"{data['month_name']} {selected_year}"])
    writer.writerow(['Currency', current_user.currency])
    writer.writerow([])

    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Income', f"{data['total_income']:.2f}"])
    writer.writerow(['Total Expenses', f"{data['total_expenses']:.2f}"])
    writer.writerow(['Net Balance', f"{data['net_balance']:.2f}"])
    writer.writerow(['Savings Rate', f"{data['savings_rate']:.1f}%"])
    writer.writerow(['Financial Health Score', f"{data['health_score']}/100"])
    writer.writerow([])

    writer.writerow(['Category Breakdown'])
    writer.writerow(['Category', 'Amount Spent', 'Percentage of Outflow'])
    for cat in data['category_breakdown']:
        writer.writerow([cat['category'], f"{cat['amount']:.2f}", f"{cat['percentage']:.1f}%"])
    writer.writerow([])

    writer.writerow(['Budget Performance'])
    writer.writerow(['Category', 'Budget Limit', 'Actual Spent', 'Remaining', 'Status'])
    for b in data['budgets']:
        writer.writerow([b['category'], f"{b['limit']:.2f}", f"{b['spent']:.2f}", f"{b['remaining']:.2f}", b['status']])

    csv_data = output.getvalue()
    filename = f"finwise_summary_{selected_year}_{selected_month:02d}.csv"

    response = make_response(csv_data)
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response
