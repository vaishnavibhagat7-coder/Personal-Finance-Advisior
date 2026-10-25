import os
from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    debug = os.environ.get('FLASK_DEBUG', '1').lower() in ('1', 'true', 't')

    print("\n" + "="*60)
    print("  🚀 FinWise AI - Personal Finance Advisor Bot")
    print("  Your money. Your goals. Your future.")
    print("="*60)
    print(f"  Local Development Server: http://{host}:{port}")
    print(f"  Demo Account: demo@finwise.ai / Demo@12345")
    print(f"  Run 'python seed_demo.py' to generate fresh 6-month demo data")
    print("="*60 + "\n")

    app.run(host=host, port=port, debug=debug)
