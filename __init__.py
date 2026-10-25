import os
import re
from flask import Flask, render_template
from config import config
from app.extensions import db, login_manager, csrf
from app.utils import format_currency, format_indian_number, format_percentage, seed_default_categories


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register custom Jinja template filters
    @app.template_filter('currency')
    def currency_filter(amount, symbol=None):
        if symbol is None:
            from flask_login import current_user
            symbol = getattr(current_user, 'currency', '₹') if current_user.is_authenticated else '₹'
        return format_currency(amount, symbol)

    @app.template_filter('indian_format')
    def indian_number_filter(amount):
        return format_indian_number(amount)

    @app.template_filter('percentage')
    def percentage_filter(val):
        return format_percentage(val)

    @app.template_filter('markdown')
    def markdown_filter(text):
        if not text:
            return ""
        # Simple and safe markdown converter for AI insight text without extra external dependencies
        # Convert headers
        t = re.sub(r'^### (.*?)$', r'<h5 class="fw-bold mt-3 mb-2 text-primary">\1</h5>', text, flags=re.M)
        t = re.sub(r'^#### (.*?)$', r'<h6 class="fw-bold mt-2 mb-1 text-secondary">\1</h6>', t, flags=re.M)
        # Convert bold
        t = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', t)
        # Convert italics
        t = re.sub(r'\*(.*?)\*', r'<em>\1</em>', t)
        # Convert blockquote
        t = re.sub(r'^> (.*?)$', r'<blockquote class="border-start border-4 border-primary ps-3 my-2 text-muted fst-italic">\1</blockquote>', t, flags=re.M)
        # Convert bullet points
        lines = t.split('\n')
        out_lines = []
        in_list = False
        for line in lines:
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                if not in_list:
                    out_lines.append('<ul class="mb-2 ps-3">')
                    in_list = True
                content = line.strip()[2:]
                out_lines.append(f'<li>{content}</li>')
            else:
                if in_list:
                    out_lines.append('</ul>')
                    in_list = False
                if line.strip():
                    out_lines.append(f'<p class="mb-2">{line.strip()}</p>')
        if in_list:
            out_lines.append('</ul>')
        return "\n".join(out_lines)

    # Register Blueprints
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.finance.routes import finance_bp
    from app.budgets.routes import budgets_bp
    from app.advisor.routes import advisor_bp
    from app.reports.routes import reports_bp
    from app.goals.routes import goals_bp
    from app.profile.routes import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(advisor_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(profile_bp)

    # Register Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    # Ensure tables and default categories exist on app context creation
    with app.app_context():
        db.create_all()
        from app.models import ExpenseCategory
        seed_default_categories(db.session, ExpenseCategory)

    # Register CLI commands
    @app.cli.command('init-db')
    def init_db():
        """Initialize database and seed default categories."""
        db.create_all()
        from app.models import ExpenseCategory
        seed_default_categories(db.session, ExpenseCategory)
        print("Database initialized successfully with default categories.")

    @app.cli.command('seed-demo')
    def seed_demo_command():
        """Seed realistic 6-month demonstration data."""
        from seed_demo import seed_demo_data
        seed_demo_data(app)
        print("Demo data seeded successfully for demo@finwise.ai.")

    @app.cli.command('reset-demo')
    def reset_demo_command():
        """Cleanly reset demo account data without affecting other users."""
        from seed_demo import reset_demo_data
        reset_demo_data(app)
        print("Demo account data reset successfully.")

    return app
