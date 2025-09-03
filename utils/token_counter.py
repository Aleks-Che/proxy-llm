import tiktoken
from config import config as Config

class TokenCounter:
    def __init__(self):
        self.encodings = {
            "deepseek": tiktoken.get_encoding("cl100k_base"),  # DeepSeek использует cl100k_base как OpenAI
            "moonshot": tiktoken.get_encoding("cl100k_base")   # Moonshot тоже
        }

    def count_tokens(self, text, provider):
        encoding = self.encodings.get(provider, tiktoken.get_encoding("cl100k_base"))
        return len(encoding.encode(text))

    def estimate_cost(self, input_tokens, output_tokens, provider, cache_hit=True):
        """Расчет стоимости на основе провайдера и типов токенов"""
        if provider not in Config.PRICES:
            return 0.0  # Для local провайдера стоимость не рассчитывается

        prices = Config.PRICES[provider]

        # Определяем тип input токенов
        input_price = prices["input_cache_hit"] if cache_hit else prices["input_cache_miss"]
        output_price = prices["output"]

        # Расчет стоимости (цены уже даны за токен)
        input_cost = input_tokens * input_price
        output_cost = output_tokens * output_price

        return input_cost + output_cost