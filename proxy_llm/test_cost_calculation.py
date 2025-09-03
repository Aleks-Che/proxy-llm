#!/usr/bin/env python3
"""
Тест для проверки расчета стоимости
"""

from utils.token_counter import TokenCounter
from config import config as Config

def test_cost_calculation():
    """Тестирование расчета стоимости"""
    counter = TokenCounter()

    # Тест для DeepSeek
    print("=== Тест DeepSeek ===")
    input_tokens = 100000  # 100k токенов для заметной стоимости
    output_tokens = 50000

    # Cache hit
    cost_hit = counter.estimate_cost(input_tokens, output_tokens, "deepseek", cache_hit=True)
    print(f"DeepSeek cache hit: {input_tokens} input + {output_tokens} output = ${cost_hit:.6f}")
    print(f"  Debug: input_cost = {input_tokens} * {Config.PRICES['deepseek']['input_cache_hit']} = {input_tokens * Config.PRICES['deepseek']['input_cache_hit']}")
    print(f"  Debug: output_cost = {output_tokens} * {Config.PRICES['deepseek']['output']} = {output_tokens * Config.PRICES['deepseek']['output']}")

    # Cache miss
    cost_miss = counter.estimate_cost(input_tokens, output_tokens, "deepseek", cache_hit=False)
    print(f"DeepSeek cache miss: {input_tokens} input + {output_tokens} output = ${cost_miss:.6f}")

    # Тест для Moonshot
    print("\n=== Тест Moonshot ===")
    cost_hit = counter.estimate_cost(input_tokens, output_tokens, "moonshot", cache_hit=True)
    print(f"Moonshot cache hit: {input_tokens} input + {output_tokens} output = ${cost_hit:.6f}")

    cost_miss = counter.estimate_cost(input_tokens, output_tokens, "moonshot", cache_hit=False)
    print(f"Moonshot cache miss: {input_tokens} input + {output_tokens} output = ${cost_miss:.6f}")

    # Тест для local (должен быть 0)
    print("\n=== Тест Local ===")
    cost_local = counter.estimate_cost(input_tokens, output_tokens, "local")
    print(f"Local: {input_tokens} input + {output_tokens} output = ${cost_local:.6f}")

    # Проверка цен из config
    print("\n=== Цены из config.py ===")
    print("DeepSeek prices:", Config.PRICES["deepseek"])
    print("Moonshot prices:", Config.PRICES["moonshot"])

if __name__ == "__main__":
    test_cost_calculation()