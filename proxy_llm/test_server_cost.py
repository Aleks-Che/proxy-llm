#!/usr/bin/env python3
"""
Тест для проверки интеграции расчета стоимости в сервер
"""

import requests
import json
import time

def test_server_cost():
    """Тестирование расчета стоимости через API сервера"""

    # URL сервера
    base_url = "http://localhost:8000"

    # Тестовый запрос
    test_request = {
        "model": "test",
        "messages": [
            {"role": "user", "content": "Hello world! " * 100}  # Длинное сообщение для заметной стоимости
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }

    try:
        # Получить начальную статистику
        response = requests.get(f"{base_url}/stats")
        if response.status_code == 200:
            initial_stats = response.json()
            print(f"Начальная статистика: {initial_stats}")
        else:
            print("Сервер не запущен")
            return

        # Отправить тестовый запрос
        print("\nОтправка тестового запроса...")
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=test_request,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Ответ получен: {result['usage']}")

            # Получить обновленную статистику
            response = requests.get(f"{base_url}/stats")
            if response.status_code == 200:
                final_stats = response.json()
                print(f"Финальная статистика: {final_stats}")

                cost_increase = final_stats['total_cost'] - initial_stats['total_cost']
                print(f"Увеличение стоимости: ${cost_increase:.6f}")

        else:
            print(f"Ошибка запроса: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_server_cost()