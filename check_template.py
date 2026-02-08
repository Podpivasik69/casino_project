import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from django.template.loader import get_template

try:
    t = get_template('crash.html')
    print("✓ Template loaded successfully")
except Exception as e:
    print(f"✗ Template error: {e}")
