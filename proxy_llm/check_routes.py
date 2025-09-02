#!/usr/bin/env python3
"""
Скрипт для проверки маршрутов FastAPI
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from server import app
    print("=== Доступные маршруты ===")

    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = list(route.methods)
            path = route.path
            print(f"{methods} {path}")
        elif hasattr(route, 'path'):
            print(f"ROUTE {route.path}")

    print("\n=== V1 маршруты ===")
    if hasattr(app, 'router') and hasattr(app.router, 'routes'):
        for route in app.router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = list(route.methods)
                path = route.path
                print(f"{methods} {path}")

except Exception as e:
    print(f"Ошибка при проверке маршрутов: {e}")
    import traceback
    traceback.print_exc()