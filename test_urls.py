"""
Simple script to test URL configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from django.urls import get_resolver

def show_urls(urlpatterns, prefix=''):
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            # This is an include()
            show_urls(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            # This is a regular path()
            print(f"{prefix}{pattern.pattern} -> {pattern.callback.__name__ if pattern.callback else 'N/A'}")

if __name__ == '__main__':
    resolver = get_resolver()
    print("=" * 60)
    print("URL Configuration")
    print("=" * 60)
    show_urls(resolver.url_patterns)
    print("=" * 60)
