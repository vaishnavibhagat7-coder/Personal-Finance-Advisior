from datetime import datetime, date
from decimal import Decimal
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager
from app.utils import to_decimal


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    
    # Financial profile
    occupation = db.Column(db.String(50), default='Salaried Professional')
    currency = db.Column(db.String(10), default='₹')
    monthly_income_target = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    monthly_savings_target = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    financial_priorities = db.Column(db.Text, nullable=True)
    financial_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    incomes = db.relationship('Income', backref='user', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')
    savings_goals = db.relationship('SavingsGoal', backref='user', lazy=True, cascade='all, delete-orphan')
    contributions = db.relationship('SavingsContribution', backref='user', lazy=True, cascade='all, delete-orphan')
    custom_categories = db.relationship('ExpenseCategory', backref='user', lazy=True, cascade='all, delete-orphan')
    ai_insights = db.relationship('AIInsight', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50), default='bi-tag')
    color = db.Column(db.String(20), default='#6366f1')
    is_default = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)

    expenses = db.relationship('Expense', backref='category', lazy=True)
    budgets = db.relationship('Budget', backref='category', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ExpenseCategory {self.name}>'


class Income(db.Model):
    __tablename__ = 'incomes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    source = db.Column(db.String(50), nullable=False)  # Salary, Freelance, Allowance, Business, Investments, Other
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Income {self.source}: {self.amount}>'


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id', ondelete='RESTRICT'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    payment_method = db.Column(db.String(50), default='UPI')  # UPI, Cash, Credit Card, Debit Card, Net Banking, Other
    merchant = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Expense {self.merchant or self.category_id}: {self.amount}>'


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id', ondelete='CASCADE'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    amount_limit = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category_id', 'month', 'year', name='_user_category_month_year_uc'),
        db.Index('idx_budget_user_month_year', 'user_id', 'year', 'month'),
    )

    def __repr__(self):
        return f'<Budget {self.category_id} ({self.month}/{self.year}): {self.amount_limit}>'


class SavingsGoal(db.Model):
    __tablename__ = 'savings_goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Numeric(12, 2), nullable=False)
    current_amount = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    target_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='In Progress')  # In Progress, Completed, Paused
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contributions = db.relationship('SavingsContribution', backref='goal', lazy=True, cascade='all, delete-orphan')

    @property
    def progress_percentage(self):
        target = to_decimal(self.target_amount)
        current = to_decimal(self.current_amount)
        if target <= Decimal('0.00'):
            return Decimal('100.0')
        ratio = (current / target) * Decimal('100.0')
        return min(Decimal('100.0'), ratio)

    @property
    def remaining_amount(self):
        target = to_decimal(self.target_amount)
        current = to_decimal(self.current_amount)
        rem = target - current
        return max(Decimal('0.00'), rem)

    @property
    def months_remaining(self):
        if not self.target_date:
            return None
        today = date.today()
        if self.target_date <= today:
            return 0
        diff_months = (self.target_date.year - today.year) * 12 + (self.target_date.month - today.month)
        return max(1, diff_months)

    @property
    def suggested_monthly_contribution(self):
        months = self.months_remaining
        if not months or months <= 0:
            return self.remaining_amount
        rem = self.remaining_amount
        if rem <= Decimal('0.00'):
            return Decimal('0.00')
        return to_decimal(rem / Decimal(str(months)))

    def __repr__(self):
        return f'<SavingsGoal {self.name}: {self.current_amount}/{self.target_amount}>'


class SavingsContribution(db.Model):
    __tablename__ = 'savings_contributions'

    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('savings_goals.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SavingsContribution Goal:{self.goal_id} Amount:{self.amount}>'


class AIInsight(db.Model):
    __tablename__ = 'ai_insights'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    prompt_type = db.Column(db.String(50), default='monthly_summary')
    content = db.Column(db.Text, nullable=False)
    health_score = db.Column(db.Integer, nullable=True)  # 0 to 100
    is_live_ai = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AIInsight User:{self.user_id} ({self.month}/{self.year})>'
