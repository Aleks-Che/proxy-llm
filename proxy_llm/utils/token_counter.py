import tiktoken

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
        prices = {
            "deepseek": {
                "input": 0.07 if cache_hit else 0.56,  # per 1M tokens
                "output": 1.68
            },
            "moonshot": {
                "input": 0.15 if cache_hit else 0.60,
                "output": 2.50
            }
        }
        price_data = prices.get(provider, prices["deepseek"])
        input_cost = (input_tokens / 1_000_000) * price_data["input"]
        output_cost = (output_tokens / 1_000_000) * price_data["output"]
        return input_cost + output_cost