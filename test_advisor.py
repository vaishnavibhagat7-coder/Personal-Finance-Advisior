from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock
from app.advisor.service import aggregate_user_financial_data, query_gemini_advisor, answer_financial_chat
from app.models import Income, Expense, ExpenseCategory, Budget
from app.extensions import db


def test_aggregate_financial_data(app, user_a):
    """Test deterministic Python calculation of financial metrics."""
    today = date.today()
    with app.app_context():
        # Add income: 50,000
        db.session.add(Income(user_id=user_a.id, source='Salary', amount=Decimal('50000.00'), date=today))
        # Add expense: 15,000 Food & Dining
        cat = ExpenseCategory.query.filter_by(name='Food & Dining').first()
        db.session.add(Expense(user_id=user_a.id, category_id=cat.id, amount=Decimal('15000.00'), date=today))
        db.session.commit()

        data = aggregate_user_financial_data(user_a, today.year, today.month)
        assert data['total_income'] == Decimal('50000.00')
        assert data['total_expenses'] == Decimal('15000.00')
        assert data['net_balance'] == Decimal('35000.00')
        assert data['savings_rate'] == Decimal('70.0')
        assert data['health_score'] >= 70
        assert len(data['category_breakdown']) == 1
        assert data['category_breakdown'][0]['category'] == 'Food & Dining'


def test_rule_based_fallback_advisor(app, user_a):
    """Test advisory generation when GEMINI_API_KEY is unset (fallback mode)."""
    today = date.today()
    with app.app_context():
        db.session.add(Income(user_id=user_a.id, source='Salary', amount=Decimal('8000.00'), date=today))
        cat_food = ExpenseCategory.query.filter_by(name='Food & Dining').first()
        cat_trans = ExpenseCategory.query.filter_by(name='Transportation').first()
        db.session.add(Expense(user_id=user_a.id, category_id=cat_food.id, amount=Decimal('3000.00'), date=today))
        db.session.add(Expense(user_id=user_a.id, category_id=cat_trans.id, amount=Decimal('2000.00'), date=today))
        db.session.commit()

        data = aggregate_user_financial_data(user_a, today.year, today.month)
        advice, is_live_ai = query_gemini_advisor(data)

        # In testing config, GEMINI_API_KEY is empty string
        assert is_live_ai is False
        assert "FinWise Rule-Based Advisory Engine" in advice or "Financial Health" in advice
        assert "Emergency Fund Target" in advice


def test_interactive_chat_endpoint(auth_client_a, app, user_a):
    """Test the /advisor/chat interactive endpoint."""
    today = date.today()
    with app.app_context():
        db.session.add(Income(user_id=user_a.id, source='Salary', amount=Decimal('40000.00'), date=today))
        db.session.commit()

    res = auth_client_a.post('/advisor/chat', json={
        'message': 'Where did most of my money go?',
        'year': today.year,
        'month': today.month
    })
    assert res.status_code == 200
    data = res.get_json()
    assert 'reply' in data
    assert len(data['reply']) > 0
    assert 'is_live_ai' in data


def test_mocked_gemini_live_call(app, user_a):
    """Test Gemini API client invocation when configured with mock."""
    today = date.today()
    with app.app_context():
        app.config['GEMINI_API_KEY'] = 'fake-test-key-mock'
        data = aggregate_user_financial_data(user_a, today.year, today.month)

        mock_genai = MagicMock()
        mock_client_cls = MagicMock()
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Mocked live Gemini financial guidance: allocate 20% to emergency fund."
        mock_instance.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_instance
        mock_genai.Client = mock_client_cls

        with patch.dict('sys.modules', {'google': MagicMock(genai=mock_genai), 'google.genai': mock_genai}):
            advice, is_live = query_gemini_advisor(data)
            assert is_live is True
            assert "Mocked live Gemini financial guidance" in advice
